fn main() {
    let (mut q, mut p): (i64, i64) = (100000000, 0);
    for _ in 0..100000 {
        for _ in 0..1000 {
            p -= 10 * q / 2000; q += p; p -= 10 * q / 2000;
            p = p - p / 4096;
        }
    }
    println!("Phase({}, {})", q, p);
}
