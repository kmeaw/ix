{% extends '//mix/template/autohell.sh' %}

{% block fetch %}
# url https://ftp.gnu.org/gnu/readline/readline-8.1.tar.gz
# md5 e9557dd5b1409f5d7b37ef717c64518e
{% endblock %}

{% block deps %}
# lib lib/ncurses
# bld dev/build/make env/std
{% endblock %}

{% block cflags %}
export CPPFLAGS="-Dxmalloc=rl_xmalloc -Dxrealloc=Drl_xrealloc ${CPPFLAGS}"
{% endblock %}

{% block coflags %}
--with-curses
{% endblock %}

{% block env %}
export COFLAGS="--with-installed-readline=${out} --with-readline=${out} \${COFLAGS}"
{% endblock %}
