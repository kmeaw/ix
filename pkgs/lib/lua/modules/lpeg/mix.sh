{% extends '//mix/template/c_std.sh' %}

{% block fetch %}
http://www.inf.puc-rio.br/~roberto/lpeg/lpeg-1.0.2.tar.gz
d342571886f1abcb7afe6a83d024d583
{% endblock %}

{% block lib_deps %}
lib/c/mix.sh
{% endblock %}

{% block bld_libs %}
lib/lua/mix.sh
{% endblock %}

{% block build %}
for x in *.c; do
    cc -c ${x}
done

ar qs liblpeg.a *.o
{% endblock %}

{% block install %}
mkdir -p ${out}/lib ${out}/share/lua
cp liblpeg.a ${out}/lib/
cp *.lua ${out}/share/lua/
nm liblpeg.a | grep luaopen_ > ${out}/share/lua/mod
{% endblock %}

{% block env %}
export LUA_PATH="${out}/share/lua:\${LUA_PATH}"
{% endblock %}
