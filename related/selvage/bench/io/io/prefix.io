prefixSum := method(a, for(i, 1, a size - 1, a atPut(i, a at(i) + a at(i - 1))); a)
prefixSumInverse := method(a, for(i, a size - 1, 1, -1, a atPut(i, a at(i) - a at(i - 1))); a)
a := List clone
for(i, 0, 99999, a append(i % 1000))
3 repeat(prefixSum(a); prefixSumInverse(a))
a sum println
prefixSum(a) last println
