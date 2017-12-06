int mss(int *a, int n){
    int mss = 0;
    int mts = 0;
    int sum = 0;
    int rand[n];
    for(int i = 0; i < n; i++){
        for(int j = 0; j < n; j++) {
            for(int k = 0; k < n; k++) {
                sum += a[i][j][k];
            }
        }
    }
    for(int i2 = 0; i2 < n; i2++){
        for(int j2 = 0; j2 < n; j2++) {
            for(int k2 = 0; k2 < n; k2++) {
                rand[i2] = a[j2] + a[k2];
            }
        }
    }
    return mss;
}

int main(int argc, char** argv){
    int n = 1000;
    int* a;
    a = malloc(n * sizeof(a));
    return mss(a, n);
}