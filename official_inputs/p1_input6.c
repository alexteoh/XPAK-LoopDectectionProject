void input6_dummy_with_deps0(int* a, int m, int n){

  for (i = 0; i < n; i++) {
    for (j = 0; j < m; j++) {
      a[i] = a[i - 2] + a[i-1] + a[i];
    }
  }
}

void input6_dummy_with_deps1(int* a, int m, int n){

  for (i = 0; i < n; i++) {
    for (j = 0; j < m; j++) {
      a[i] = a[i - 1] + a[i] + a[i + 1];
    }
  }
}

void input6_dummy_with_deps2(int* a, int m, int n){
  for (i = 0; i < n; i++) {
    for (j = 0; j < m; j++) {
      a[i] = a[i - 1] + a[i] + a[i + 1];
    }
  }
}

void input6_dummy_with_deps3(int* a, int m, int n){
  for (i = 0; i < n; i++) {
    for (j = 0; j < m; j++) {
      a[i] = a[i + 1] + a[i] + a[i + 2];
    }
  }
}



void input6_matvec(int** a, int* b, int* c, int n) {
  int i, j;
  for (i = 0; i < n; i++) {
    for (j = 0; j < n; j++) {
      c[i] = c[i] + a[i][j] * b[j];
    }
  }
}
