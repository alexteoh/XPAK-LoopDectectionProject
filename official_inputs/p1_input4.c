int input4_max_tail_sum(int* a, int n){
  int i;
  int mts;
  mts = 0;
  for(i = 0; i < n; i++){
    mts = max(mts + a[i], 0);
  }
  return mts;
}

int input4_max_prefix_sum(int *a, int n){
  int i;
  int mps, sum;
  mps = 0;
  sum = 0;
  for(i = 0; i< n; i++){
    sum += a[i];
    mps = max(mps, sum);
  }
  return mps;
}
