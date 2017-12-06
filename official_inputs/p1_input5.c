int input5_example_max_len_1s (int *a, int n) {
  int cl = 0;
  int ml = 0;
  int c = 0;
  int conj = 1;

  for (int i = 0; i < n; i++) {
    cl = a[i] ? cl + 1 : 0;
    ml = max (ml, cl);
    conj = conj && a[i];
    c = c + (conj ? 1 : 0);
  }

  if(conj && ml != n){
    return -1;
  }
  return ml;
}


int main()
{
  int n = 10;
  int i, sum = 0;

  for ( i = 1; i <= 10; i++ ) {
    sum += i;
  }

  return sum;
}
