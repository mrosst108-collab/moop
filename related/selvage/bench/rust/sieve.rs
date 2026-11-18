fn main() {
    let n: i64 = 50_000_000;
    let mut composite = vec![false; n as usize];
    let mut count: i64 = 0;
    for i in 2..n {
        if !composite[i as usize] {
            count += 1;
            let mut j = i * i;
            while j < n { composite[j as usize] = true; j += i; }
        }
    }
    println!("{}", count);
}
