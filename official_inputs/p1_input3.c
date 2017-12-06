int input3_test_types (float *a, int n) {
  _Bool b;
  int k, l;
  float f;
  f = 1;
  for(k = 0; k < n; k++){
    f = cos(a[0] - f);
    b = b && f > 0.0;
    k =+ floor(f);
  }
  return (b ? k : k-1);
}

int main()
{
  return 0;
}
