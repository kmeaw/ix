{% extends '//die/go/pure.sh' %}

{% block go_url %}
https://github.com/rs/curlie/archive/refs/tags/v1.6.9.tar.gz
{% endblock %}

{% block go_sum %}
sha:95b7061861aa8d608f9df0d63a11206f8cd532295ca13dd39ed37e0136bdcc5f
{% endblock %}

{% block go_sha %}
sha:18adf1faf09781224b3d9d7d7986fda86de2e8ebaf600d29e2281decd2d89e2e
{% endblock %}

{% block patch %}
rm curlie
{% endblock %}

{% block install %}
mkdir ${out}/bin
cp curlie ${out}/bin/
{% endblock %}
