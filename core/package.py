import os
import sys
import jinja2
import multiprocessing

import core.sh_cmd as cs
import core.utils as cu
import core.error as ce


class FileLoader:
    def __init__(self, pkg):
        self._p = pkg

    def __getattr__(self, name):
        fname = name.replace('_', '.')

        return {
            'kind': fname.split('.')[-1],
            'data': self._p.template(fname),
        }


def fmt_sel(s):
    return str(s)


def exec_mod(text, iface):
    g = {}

    exec(text, g)

    return g['package'](iface)


BUILD_PY_SCRIPT = '''
import atexit

mix.header()
atexit.register(mix.footer)

# suc
{build_script}
# euc
'''.strip()


FETCH_SRC_SCRIPT = '''
import sys

md5 = sys.argv[-1]
out = sys.argv[-2]

def fetch():
    for url in sys.argv[1:-2]:
        try:
            mix.fetch_url(url, out)

            return True
        except Exception as e:
            print(f'fetch failed: {e}')

try:
    if not fetch():
        raise Exception(f'all attemps failed')

    mix.check_md5(out, md5)
except Exception as e:
    print(f'can not fetch {out}: {e}')
    sys.exit(1)
'''.strip()


LINK_SRCS_SCRIPT = '''
import sys
import os

os.chdir(os.environ['out'])

for f in sys.argv[1:]:
    os.link(f, os.path.basename(f))
'''.strip()


def compile_sh(script):
    return cs.parse(script)


def cononize(v):
    s = v.replace('\n', ' ').replace('\\', ' ').strip()

    while '  ' in s:
        s = s.replace('  ', ' ')

    return s


class Package:
    def __init__(self, selector, mngr):
        self.selector = selector
        self.manager = mngr

        try:
            try:
                self._d = exec_mod(self.template('package.py'), self)
            except FileNotFoundError:
                self._d = compile_sh(self.template('package.sh'))
        except FileNotFoundError as e:
            raise ce.Error(f'can not load {self.name}', exception=e)
        except cs.Error as e:
            text = f'can not render {self.name}'
            context = f'{e.lineno}: {e.line}'

            raise ce.Error(text, context=context, exception=e.slave)

        self._u = cu.struct_hash([self._d, list(self.iter_env())])

    @property
    def flags(self):
        return self.selector.get('flags', {})

    def prepare_deps(self, v):
        return cononize(v)

    def dep_list(self, v, prefix):
        def iter_lines():
            for l in v.splitlines():
                l = l.strip()

                if l:
                    yield '# ' + prefix + ' ' + l

        return '\n'.join(iter_lines()).strip() + '\n'

    @property
    def os(self):
        return self.platform['target']['os']

    def if_linux(self, v):
        return self.if_os(v, 'linux')

    def if_darwin(self, v):
        return self.if_os(v, 'darwin')

    def if_os(self, v, os):
        if self.os == os:
            return v

        return ''

    def template(self, name):
        path = os.path.join(self.name, name)
        tmpl = self.manager.env.get_template(path)

        try:
            return self.strip_template(tmpl.render(mix=self))
        except Exception as e:
            raise ce.Error(f'can not render {path}', exception=e)

    def strip_template(self, v):
        vv = v.replace('\n\n\n', '\n\n')

        if vv == v:
            return v

        return self.strip_template(vv)

    @property
    def platform(self):
        return self.config.platform

    @property
    def descr(self):
        return self._d

    @property
    def name(self):
        return self.selector['name']

    @property
    def config(self):
        return self.manager.config

    @property
    def where(self):
        return os.path.join(self.config.where, self.name)

    @property
    def urls(self):
        return self.descr.get('build', {}).get('fetch', [])

    @property
    @cu.cached_method
    def files(self):
        return FileLoader(self)

    @property
    def uid(self):
        return self._u

    @property
    @cu.cached_method
    def out_dir(self):
        return self.config.store_dir + '/' + self.uid + '-' + self.name.replace('/', '-')

    @property
    @cu.cached_method
    def tmp_dir(self):
        return self.config.build_dir + '/' + self.uid

    def src_dir_for(self, url):
        return self.config.store_dir + '/' + cu.struct_hash(url)

    @property
    def src_dir(self):
        return self.src_dir_for(self.descr['build']['fetch'])

    def load_package(self, selector):
        try:
            return self.manager.load_package(selector)
        except FileNotFoundError:
            s1 = fmt_sel(selector)
            s2 = fmt_sel(self.selector)

            raise ce.Error(f'can not load dependant package {s1} of {s2}')

    def filter_buildable(self, it):
        for n in it:
            if self.load_package(n).buildable():
                yield n

    def make_selector(self, lst):
        def make(v):
            try:
                v['name']
            except Exception:
                v = {'name': v}

            return v

        return [make(x) for x in lst]

    # build
    def build_depends(self):
        return self.make_selector(self.descr.get('build', {}).get('depends', []))

    @cu.cached_method
    def all_build_depends(self):
        def iter_deps():
            yield from self.build_depends()

            for d in self.build_depends():
                yield from self.load_package(d).all_runtime_depends()

        return cu.uniq_list(self.filter_buildable(iter_deps()))

    def iter_all_build_depends(self):
        for d in self.all_build_depends():
            yield self.load_package(d)

    # runtime
    def runtime_depends(self):
        return self.make_selector(self.descr.get('runtime', {}).get('depends', []))

    @cu.cached_method
    def all_runtime_depends(self):
        def iter_deps():
            yield from self.runtime_depends()

            for d in self.runtime_depends():
                yield from self.load_package(d).all_runtime_depends()

        return cu.uniq_list(self.filter_buildable(iter_deps()))

    def iter_all_runtime_depends(self):
        for d in self.all_runtime_depends():
            yield self.load_package(d)

    # all
    def depends(self):
        return self.build_depends() + self.runtime_depends()

    @cu.cached_method
    def all_depends(self):
        def iter_deps():
            for d in self.depends():
                yield d
                yield from self.load_package(d).all_depends()

        return cu.uniq_list(iter_deps())

    def iter_env(self):
        path = ['/nowhere']

        for p in self.iter_all_build_depends():
            od = p.out_dir

            yield p.name.replace('-', '_').replace('/', '_'), od

            path.append(od + '/bin')

        yield 'PATH', ':'.join(path)

    def build_sh_script(self, data, env):
        return {
            'args': ['dash', '-s'],
            'stdin': data,
            'env': env,
        }

    def build_py_script(self, data, env, args=[]):
        return {
            'args': [sys.executable, self.config.binary, 'misc', 'runpy'] + args,
            'stdin': BUILD_PY_SCRIPT.replace('{build_script}', data),
            'env': env,
        }

    def build_script(self):
        def iter_env():
            yield from self.iter_env()

            if 'fetch' in self._d['build']:
                yield 'src', self.src_dir

            yield 'out', self.out_dir
            yield 'tmp', self.tmp_dir
            yield 'mix', self.config.binary
            yield 'exe', sys.executable

            yield 'make_thrs', str(multiprocessing.cpu_count() + 2)

        build = self.descr['build']['script']

        return {
            'sh': self.build_sh_script,
            'py': self.build_py_script,
        }[build['kind']](build['data'], dict(iter_env()))

    def fetch_src_script(self, urls, out, md5):
        path = os.path.join(self.src_dir_for([out, md5]), out)

        def iter_env():
            yield from self.iter_env()

            yield 'out', os.path.dirname(path)

        return self.build_py_script(FETCH_SRC_SCRIPT, dict(iter_env()), urls + [path, md5])

    def empty_script(self):
        return self.build_py_script('', dict(out=self.out_dir))

    def empty_command(self):
        script = self.empty_script()

        return {
            'out_dir': [script['env']['out']],
            'cmd': [script],
        }

    def link_srcs_script(self, files, out):
        def iter_env():
            yield from self.iter_env()

            yield 'out', out

        return self.build_py_script(LINK_SRCS_SCRIPT, dict(iter_env()), files)

    def buildable(self):
        try:
            self.descr['build']['script']
        except KeyError:
            return False

        return True

    def iter_commands(self):
        if not self.buildable():
            yield self.empty_command()

            return

        extra = []

        for ui in self.descr['build'].get('fetch', []):
            md5 = ui.get('md5', '')
            url = ui['url']
            urls = ['https://storage.yandexcloud.net/mix-cache/cache/' + md5, url]
            script = self.fetch_src_script(urls, os.path.basename(url), md5)
            path = script['args'][-2]

            cmd = {
                'out_dir': [os.path.dirname(path)],
                'cmd': [script],
                'path': path,
            }

            yield cmd

            extra.append(cmd)

        if extra:
            script = self.link_srcs_script([x['path'] for x in extra], self.src_dir)

            cmd = {
                'in_dir': sum([x['out_dir'] for x in extra], []),
                'out_dir': [script['env']['out']],
                'cmd': [script],
            }

            yield cmd

            extra = cmd['out_dir']

        yield {
            'in_dir': [x.out_dir for x in self.iter_all_build_depends()] + extra,
            'out_dir': [self.out_dir],
            'cmd': [self.build_script()],
        }

    def commands(self):
        return list(self.iter_commands())

    def install(self, to):
        fr = self.out_dir

        for x in cu.iter_dir(fr):
            if '/' not in x:
                continue

            p = os.path.join(to, x)

            try:
                os.makedirs(os.path.dirname(p))
            except Exception:
                pass

            try:
                os.unlink(p)
            except FileNotFoundError:
                pass

            os.symlink(os.path.join(fr, x), p)
