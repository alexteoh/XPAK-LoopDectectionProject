float input2_simple_loop_with_array (float *a, int n) {
  int i;
  i = 0;
  float sumfloat;
  sumfloat = 0.0;
  for(i = 0; i< n; i++) {
    sumfloat += a[i];
  }
  return sumfloat;
}

int main(int argc, char **argv) {
  return 0;
}
