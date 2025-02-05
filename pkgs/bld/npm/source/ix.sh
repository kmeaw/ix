{% extends '//die/std/ix.sh' %}

{% block fetch %}
https://github.com/npm/cli/archive/refs/tags/v9.8.0.tar.gz
sha:7a6c27c9c0fe6f39069365c33a93e43f5ae2b09f80943ec9309240f809440128
{% endblock %}

{% block use_network %}true{% endblock %}

{% set sum %}e1d87aff7410f556f30fa34606bb94f2964e07ccfaee3400e51ae5e62378e39b{% endset %}

{% block predict_outputs %}
[{"path": "share/npm.tar.lz4", "sum": "{{sum}}"}]
{% endblock %}

{% block bld_tool %}
bin/nodejs
bld/stable/pack
{% endblock %}

{% block build %}
node workspaces/arborist/bin/index.js reify
node bin/npm-cli.js install
rm -rf undefined
stable_pack {{sum}} ${tmp}/npm.tar.lz4 .
{% endblock %}

{% block install %}
mkdir ${out}/share
mv ${tmp}/npm.tar.lz4 ${out}/share/
{% endblock %}

{% block env %}
export src=${out}/share/npm.tar.lz4
{% endblock %}
