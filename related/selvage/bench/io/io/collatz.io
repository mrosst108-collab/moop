chain := method(n,
    steps := 0
    while(n != 1,
        if(n % 2 == 0, n = n / 2, n = 3 * n + 1)
        steps = steps + 1
    )
    steps
)
best := 0
bestStart := 1
for(s, 1, 30000,
    c := chain(s)
    if(c > best, best = c; bestStart = s)
)
bestStart println
