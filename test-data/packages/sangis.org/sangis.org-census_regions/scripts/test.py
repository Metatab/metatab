#
#
# 

import metatab

doc = metatab.open_package('..')

r = doc.resource('sra')

for row in r.iterdict:
    
    print(row['name'],row['geometry'].shape.bounds)