fn prefix_sum(a: &mut [u64]) { for i in 1..a.len() { a[i] = a[i].wrapping_add(a[i - 1]); } }
fn prefix_sum_inv(a: &mut [u64]) { for i in (1..a.len()).rev() { a[i] = a[i].wrapping_sub(a[i - 1]); } }
fn checksum(a: &[u64]) -> u64 { let mut s = 0u64; for &x in a { s = s.wrapping_mul(31) ^ x; } s }
fn main() {
    let n = 10_000_000usize;
    let mut a: Vec<u64> = (0..n).map(|i| (i as u64).wrapping_mul(2654435761)).collect();
    for _ in 0..10 { prefix_sum(&mut a); prefix_sum_inv(&mut a); }
    println!("{}", checksum(&a));
    prefix_sum(&mut a);
    println!("{}", checksum(&a));
}
