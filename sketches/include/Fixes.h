#ifndef FIXES_H
#define FIXES_H

// Fix vector STL broken in Arduino Due
// https://forum.arduino.cc/t/arduino-due-warning-std-__throw_length_error-char-const/308515/2
namespace std
{
    void __throw_length_error(char const *) __attribute__((noreturn));
    void __throw_length_error(char const *) { while(1);}
}

#endif