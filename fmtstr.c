#include <stdio.h>
#define KEY 167
#define offset 4
#define deadbeef ((char *) 0xdeadbeef)

char msg00[] = "wow,好像被你发现了彩蛋?";
char msg01[] = "fmtstr了解一下?";
char msg1[] = "hint1: 当key=5时即可拿到flag";
char msg2[] = "很好，hint2:\nthe $ of &key = 167(也许你需要再了解一下fmtstr)";
char flag[] = "VidarTeam{Welcome_To_The_Bin_World_XD}";

int key = 23333333;

int main() {
  char *buf[1111] = {deadbeef, deadbeef, msg1, deadbeef, msg2};
  buf[KEY-offset] = &key;  // key
  gets(buf);
  printf(buf, msg00, msg01);
  printf("\n-------------\nnow the key = %d", key);

  if (key == 5) {
    puts("");
    puts(flag);
    printf("联系徐大哥(Aris)可领取奖金五毛钱 233");
  }
}