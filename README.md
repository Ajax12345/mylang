
Mylang is a dynamically typed, object orientated toy programming language, inspired by Python 3, Java, and Javascript.

### Example: summing the elements in a container:
```
l = {34, 133, 24, 424, 535, 34}
procedure sum(arlist:ArrayList){
  total = 0;
  for arlist -> i{
    total = total + i
  }
  return total
}

s = sum(l)
print s
```
myLang console OUT:  1184
