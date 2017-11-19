int mss(int *a, int n){
    int mss = 0;
    int mts = 0;
    int sum = 0;
    for(int i = 0; i < n; i++){
        for(int j = 0; j < n; j++) {
            for(int k = 0; k < n; k++) {
                sum += a[i][j][k];
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