{% extends '//mix/template/proxy.sh' %}

{% block lib_deps %}
lib/wolfssl/mix.sh
{% endblock %}

{% block bld_deps %}
env/std/mix.sh
{% endblock %}

{% block build %}
>empty.c
gcc -c empty.c -o empty.o
ar q libcrypto.a empty.o
{% endblock %}

{% block install %}
mkdir ${out}/lib && cp libcrypto.a ${out}/lib/
cp -R ${lib_wolfssl}/include/wolfssl ${out}/include
{% endblock %}

{% block env %}
export COFLAGS="--with-ssl=${out} --with-openssl=${out} --with-openssldir=${out} --with-ssl-dir=${out} \${COFLAGS}"
{% endblock %}
