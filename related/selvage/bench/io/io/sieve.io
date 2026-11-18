n := 300000
composite := List clone setSize(n)
count := 0
for(i, 2, n - 1,
    if(composite at(i) isNil,
        count = count + 1
        j := i * i
        while(j < n, composite atPut(j, true); j = j + i)
    )
)
count println
