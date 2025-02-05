{% extends '//die/std/ix.sh' %}

{% block fetch %}
https://www.uclibc.org/downloads/uClibc-0.9.33.tar.xz
sha:1588b603d87aa460eae64f097db71de534c3b9e8dd904e3989a6be82649f8bb2
{% endblock %}

{% block bld_tool %}
bld/shebangs
{% endblock %}

{% block install %}
mkdir ${out}/bin
cp extra/scripts/getent ${out}/bin/
fix_shebangs ${out}/bin/getent
{% endblock %}
