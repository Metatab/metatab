
import pandas as pd
import numpy as np
import pandasreporter as pr

b17001 = pr.get_dataframe('B17001', '140',  '05000US06073', cache=True)
b17024 = pr.get_dataframe('B17024', '140',  '05000US06073', cache=True)
b17017 = pr.get_dataframe('B17017', '140',  '05000US06073', cache=True)

print df.head(2)