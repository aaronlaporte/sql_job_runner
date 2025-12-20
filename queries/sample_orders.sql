SELECT id,
       customer_name,
       status,
       order_total,
       order_date
FROM orders
{% if start_date and end_date %}
WHERE order_date BETWEEN '{{ start_date }}' AND '{{ end_date }}'
{% endif %}
ORDER BY order_date;
