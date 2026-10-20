#include <math.h>
#include <stdlib.h>
double hmm_fb(int n, const double *e, double u, double d, double *g, double *xi) {
  double *a=malloc(2*n*sizeof(double)), *s=malloc(n*sizeof(double));
  double sum=u+d, l0=d/sum*e[0], l1=u/sum*e[1];
  s[0]=l0+l1; a[0]=l0/s[0]; a[1]=l1/s[0]; double ll=log(s[0]);
  for(int t=1;t<n;t++) {l0=((1-u)*a[2*t-2]+d*a[2*t-1])*e[2*t]; l1=(u*a[2*t-2]+(1-d)*a[2*t-1])*e[2*t+1]; s[t]=l0+l1; a[2*t]=l0/s[t];a[2*t+1]=l1/s[t];ll+=log(s[t]);}
  for(int k=0;k<4;k++)xi[k]=0;
  double b0=1,b1=1; g[n-1]=a[2*n-1];
  for(int t=n-2;t>=0;t--) {
    double z0=e[2*t+2]*b0/s[t+1],z1=e[2*t+3]*b1/s[t+1];
    xi[0]+=a[2*t]*(1-u)*z0;xi[1]+=a[2*t]*u*z1;xi[2]+=a[2*t+1]*d*z0;xi[3]+=a[2*t+1]*(1-d)*z1;
    b0=(1-u)*z0+u*z1;b1=d*z0+(1-d)*z1;
    double v0=a[2*t]*b0,v1=a[2*t+1]*b1;g[t]=v1/(v0+v1);
  }
  free(a);free(s);return ll;
}
void hmm_viterbi(int n,const double *le,double u,double d,unsigned char *path){
  unsigned char *back=malloc(2*n);double p0=log(d/(u+d))+le[0],p1=log(u/(u+d))+le[1];
  double a=log(1-u),b=log(u),c=log(d),f=log(1-d);
  for(int t=1;t<n;t++){double x0=p0+a,x1=p1+c,y0=p0+b,y1=p1+f;back[2*t]=x1>x0;back[2*t+1]=y1>y0;p0=fmax(x0,x1)+le[2*t];p1=fmax(y0,y1)+le[2*t+1];}
  path[n-1]=p1>p0;for(int t=n-2;t>=0;t--)path[t]=back[2*(t+1)+path[t+1]];free(back);
}
void hmm_path(int n,const double *r,double u,double d,unsigned char *path){
  path[0]=r[0]<u/(u+d);for(int t=1;t<n;t++)path[t]=path[t-1]?(r[t]>=d):(r[t]<u);
}
