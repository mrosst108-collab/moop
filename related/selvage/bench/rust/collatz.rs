fn chain(mut n: u64) -> u64 {
    let mut steps = 0u64;
    while n != 1 { n = if n % 2 == 0 { n / 2 } else { 3 * n + 1 }; steps += 1; }
    steps
}
fn main() {
    let (mut best, mut best_start) = (0u64, 1u64);
    for s in 1..=3_000_000u64 {
        let c = chain(s);
        if c > best { best = c; best_start = s; }
    }
    println!("{}", best_start);
}
