{% extends '//die/c/make.sh' %}

{% block lib_deps %}
lib/c
{% endblock %}

{% block bld_tool %}
bld/dlfcn
{% endblock %}

{% block script_init_env %}
export LUA_PATH=
{{super()}}
{% endblock %}

{% block patch %}
sed -e 's|.*return 0.*open failed.*|if (f == NULL) return (strstr(filename, ".so") > 0 \&\& dlopen(filename, 0) != NULL);|' \
    -i {{self.lua_dlopen().strip()}}
{% endblock %}

{% block build %}
(IFS=":"; for x in ${LUA_PATH}; do cat ${x}/mod; done) | sed -e 's|.* ||' | while read l; do
    n=$(echo ${l} | sed -e 's|.*luaopen_||')
    echo "${n} ${l} ${l}"
done | dl_stubs > dl.c

${CC} -c dl.c

{{super()}}
{% endblock %}
