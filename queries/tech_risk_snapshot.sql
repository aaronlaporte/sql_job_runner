SELECT
    assessed_on,
    business_unit,
    system_name,
    control_domain,
    risk_factor,
    inherent_risk,
    residual_risk,
    severity,
    remediation_owner,
    target_remediation,
    status
FROM technology_risk_assessments
{% if start_date %}
WHERE assessed_on >= '{{ start_date }}'
{% endif %}
{% if end_date %}
  {% if start_date %}AND{% else %}WHERE{% endif %} assessed_on <= '{{ end_date }}'
{% endif %}
ORDER BY assessed_on DESC
LIMIT {{ limit | default(100) }};
