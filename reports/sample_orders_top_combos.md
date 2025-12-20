# Top Dimension/Measure Outcomes

## Dimensions: customer_name
### Measure: order_total
```
  customer_name  sum_value  avg_value  row_count
      Liam Chen  133280.71 140.000746        952
Sebastian Gomez  132879.26 138.704864        958
   Marcus Allen  131721.84 139.093812        947
     Nadia Khan  131411.96 135.756157        968
    Priya Patel  123909.07 136.916099        905
```

## Dimensions: status
### Measure: order_total
```
   status  sum_value  avg_value  row_count
 refunded  200399.21 139.748403       1434
delivered  194360.17 138.039893       1408
  shipped  191705.53 139.931044       1370
  pending  189839.75 136.673686       1389
```

## Dimensions: order_date
### Measure: order_total
```
order_date  sum_value  avg_value  row_count
2025-09-13    2666.01 177.734000         15
2025-07-29    2485.39 165.692667         15
2025-08-07    2361.75 157.450000         15
2025-07-16    2347.09 180.545385         13
2025-09-27    2322.22 154.814667         15
```

## Dimensions: customer_name, status
### Measure: order_total
```
  customer_name    status  sum_value  avg_value  row_count
      Liam Chen  refunded   38995.66 148.272471        263
   Marcus Allen delivered   36274.58 142.253255        255
Sebastian Gomez  refunded   34922.67 140.817218        248
    Fiona Apple   shipped   34037.60 139.498361        244
      Liam Chen delivered   33715.38 139.319752        242
```

## Dimensions: customer_name, order_date
### Measure: order_total
```
customer_name order_date  sum_value  avg_value  row_count
  Fiona Apple 2025-06-17    1080.18 154.311429          7
  Priya Patel 2025-10-02    1035.29 172.548333          6
  Fiona Apple 2025-07-02    1021.64 170.273333          6
    Liam Chen 2023-08-01    1011.99 202.398000          5
 Marcus Allen 2025-09-10     995.24 165.873333          6
```

## Dimensions: status, order_date
### Measure: order_total
```
   status order_date  sum_value  avg_value  row_count
 refunded 2025-09-27    1332.07 190.295714          7
delivered 2024-09-25    1195.30 199.216667          6
  pending 2025-08-29    1182.39 197.065000          6
delivered 2025-09-10    1178.40 196.400000          6
  pending 2025-11-06    1173.65 146.706250          8
```
