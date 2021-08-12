#include <CommandAndControl.h>

#include <Init.h>


void loop_command_and_control() {
    if (S.available() != 0) {
        packet_reactor.tick();
    }
}
