#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <arpa/inet.h>

char** split_string_at(char *str, char delim);

int check_password(char *password_given, char *uname_given){
  int password_good;
  char data_buff[13];
  char text_buff[200];
  char **bits;
  char *correct_hash, *salt, *correct_uname;
  FILE *f;

  /* get the salt and the password hash from the password file */
  f = fopen("/etc/apache2/auth_prog/password", "r");
  fgets(text_buff,200,f);
  fclose(f);
  bits = split_string_at(text_buff,'\n');
  bits = split_string_at(bits[0],' ');
  correct_uname = bits[0];
  salt = bits[1];
  correct_hash = bits[2];
  
  /* is it the user we expect? */
  if(strcmp(uname_given,correct_uname) != 0)
    return 0;

  password_good = 0;

  /* concatenate the salt and the given password, and feed it into sha256 */
  strcpy(data_buff,salt);
  strcpy(data_buff+strlen(salt),password_given);
  sprintf(text_buff,"echo %s | sha256sum",data_buff);
  f = popen(text_buff,"r");
  fgets(text_buff,100,f);
  pclose(f);

  /* pull out the sha256 hash of the data and compare it to the stored hash */
  bits = split_string_at(text_buff,' ');
  if(strcmp(bits[0],correct_hash) == 0)
    password_good=1;

  return password_good;
}

int main(){
  char *password_given, *uname_given;
  int check_result;
  
  password_given = getenv("PASS");
  uname_given = getenv("USER");
  if (password_given == 0 || uname_given == 0)
    return 1;

  if(!check_password(password_given,uname_given))
    return 1;
  else
    return 0;
}

char** split_string_at(char *str, char delim){
  char **str_bits;
  int n_str_bits, str_bits_ind;
  char *con, *base;
  
  n_str_bits = 1;
  for(con = str; *con != 0; con++)
    if(*con == delim)
      n_str_bits++;
  str_bits = malloc((n_str_bits+1)*sizeof(char*));
  str_bits[n_str_bits] = 0;

  base=con=str;
  str_bits_ind=0;
  while(1){
    if ((*con == delim) || (*con == 0)){
      str_bits[str_bits_ind] = malloc(con-base+1);
      strncpy(str_bits[str_bits_ind], base, con-base);
      str_bits[str_bits_ind][con-base]=0;
      if (*con == 0)
	break;
      str_bits_ind++;
      base=con=con+1;   
    }
    else
      con++;
  }

  return str_bits;
}
