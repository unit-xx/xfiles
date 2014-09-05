con = gzcon(file('./sit.gz', 'rb'))
  source(con)
close(con)

# mean-reversion points:
# fixed period
# dispersion threshold
# sell top buy bottom