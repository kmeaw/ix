{% extends '//mix/template/autohell.sh' %}

{% block fetch %}
http://ftp.gnu.org/pub/gnu/gperf/gperf-3.1.tar.gz
9e251c0a618ad0824b51117d5d9db87e
{% endblock %}

{% block bld_deps %}
lib/c++/mix.sh
env/autohell/mix.sh
{% endblock %}
