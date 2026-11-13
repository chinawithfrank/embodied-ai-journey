#include <cassert>
#include <limits>
#include "autonomy/controller.hpp"
using namespace robot;
static Target hand(uint32_t frame, int64_t time, float x=0, float size=.35f) {
    Target t; t.valid=true; t.frame=frame; t.captured_ms=time; t.x=x; t.size=size; return t;
}
static bool stopped(Command c) { return !c.left && !c.right && !c.fan; }
static bool parked_fan(Command c) { return !c.left && !c.right && c.fan; }
int main() {
    Config legacy; legacy.turn_min_ms=legacy.turn_max_ms=100; legacy.turn_cooldown_ms=300;
    HandFollower f(legacy);
    assert(stopped(f.step(hand(1,100),100,false)));
    auto c=f.step(hand(1,100,.6f),100,true);
    assert(c.left>0 && c.right<0 && c.fan);
    assert(parked_fan(f.step(hand(1,100,.6f),200,true))); // independent pulse expiry
    assert(parked_fan(f.step(hand(1,100,.6f),600,true))); // no repeated-frame pulse
    c=f.step(hand(2,600,-.6f),600,true); assert(c.left<0 && c.right>0);
    c=f.step(hand(3,650,-.6f),650,true); assert(c.left<0); // finish existing pulse
    assert(parked_fan(f.step(hand(3,650,-.6f),700,true)));
    c=f.step(hand(4,1100,0,.15f),1100,true); assert(c.left>0 && c.right>0 && c.fan);
    c=f.step(hand(5,1600,0,.6f),1600,true); assert(c.left<0 && c.right<0 && c.fan);
    assert(parked_fan(f.step(hand(6,2100),2100,true)));
    assert(parked_fan(f.step(hand(6,2100),2150,true)));
    assert(parked_fan(f.step(hand(7,2500),2500,true)));
    c=f.step(hand(8,2900),2900,true); assert(c.fan && !c.left && !c.right);
    c=f.step(hand(9,3300,.16f,.40f),3300,true); assert(c.fan); // hysteresis
    assert(stopped(f.step(hand(9,3300),4301,true))); // inference stalled
    assert(stopped(f.step(Target{},4400,true)));
    f.reset(); auto high=hand(1,100); high.y=.7f; assert(parked_fan(f.step(high,100,true)));
    auto bad=hand(2,200); bad.x=std::numeric_limits<float>::quiet_NaN();
    assert(stopped(f.step(bad,200,true)));
    assert(stopped(f.step(hand(3,400),300,true))); // future timestamp
    Config invalid; invalid.duty=101; HandFollower broken(invalid);
    assert(stopped(broken.step(hand(1,100,.6f),100,true)));
    Config mirrored; mirrored.turn_sign=-1; HandFollower flipped(mirrored);
    c=flipped.step(hand(1,100,.6f),100,true); assert(c.left<0 && c.right>0);
    // Proportional turns persist across fresh frames, without extending the deadline.
    HandFollower adaptive;
    c=adaptive.step(hand(1,100,1),100,true); assert(c.left>0);
    c=adaptive.step(hand(2,200,.8f),200,true); assert(c.left>0);
    c=adaptive.step(hand(3,300,.7f),300,true); assert(c.left>0);
    assert(parked_fan(adaptive.step(hand(3,300,.7f),450,true))); // original 350ms cap
    assert(parked_fan(adaptive.step(hand(4,500,.7f),500,true))); // cooldown
    c=adaptive.step(hand(5,600,.7f),600,true); assert(c.left>0);
    assert(parked_fan(adaptive.step(hand(6,650,-.7f),650,true))); // crossing stops, no instant reverse
    adaptive.reset();
    c=adaptive.step(hand(1,100,.13f),100,true); assert(c.left>0);
    assert(parked_fan(adaptive.step(hand(1,100,.13f),205,true))); // near centre: about 103ms
    adaptive.reset();
    adaptive.step(hand(1,100,1),100,true);
    assert(parked_fan(adaptive.step(hand(2,200,0),200,true))); // stop early when centred
    adaptive.reset();
    adaptive.step(hand(1,100,1),100,true);
    assert(stopped(adaptive.step(Target{},150,true))); // lost target interrupts long pulse
    Config bad_turn; bad_turn.turn_max_ms=801; assert(!bad_turn.valid());
    bad_turn.turn_max_ms=350; bad_turn.stale_ms=300; assert(!bad_turn.valid());
    Config fast; fast.duty=75; fast.pulse_ms=700; fast.cooldown_ms=100;
    fast.turn_min_ms=200; fast.turn_max_ms=700; fast.turn_cooldown_ms=100;
    assert(fast.valid());
    HandFollower quicker(fast);
    c=quicker.step(hand(1,100,1),100,true); assert(c.left==75 && c.right==-75);
    c=quicker.step(hand(2,500,.9f),500,true); assert(c.left==75);
    assert(parked_fan(quicker.step(hand(2,500,.9f),800,true))); // fixed 700ms deadline
    assert(parked_fan(quicker.step(hand(3,850,.9f),850,true))); // cooldown preserved
    quicker.reset();quicker.step(hand(1,100,1),100,true);
    assert(parked_fan(quicker.step(hand(2,200,0),200,true))); // early stop when centred
    quicker.reset();quicker.step(hand(1,100,1),100,true);
    assert(stopped(quicker.step(Target{},200,true))); // invalid camera still overrides
    quicker.reset();
    c=quicker.step(hand(1,100,0,.1f),100,true); assert(c.left==75 && c.right==75);
    c=quicker.step(hand(2,500,0,.15f),500,true); assert(c.left==75 && c.right==75);
    c=quicker.step(hand(2,500,0,.15f),799,true); assert(c.left==75);
    assert(parked_fan(quicker.step(hand(2,500,0,.15f),800,true)));
    assert(parked_fan(quicker.step(hand(3,850,0,.15f),850,true)));
    c=quicker.step(hand(4,900,0,.15f),900,true); assert(c.left==75);
    quicker.reset();
    c=quicker.step(hand(1,100,0,.6f),100,true); assert(c.left==-75 && c.right==-75);
    c=quicker.step(hand(2,500,0,.55f),500,true); assert(c.left==-75 && c.right==-75);
    assert(parked_fan(quicker.step(hand(2,500,0,.55f),800,true)));
    for (auto interruption : {hand(2,300,0,.35f), hand(2,300,0,.6f), hand(2,300,.6f,.1f)}) {
        quicker.reset();quicker.step(hand(1,100,0,.1f),100,true);
        assert(parked_fan(quicker.step(interruption,300,true)));
    }
    quicker.reset();quicker.step(hand(1,100,0,.1f),100,true);
    Target lost;lost.frame=2;lost.captured_ms=300;
    assert(parked_fan(quicker.step(lost,300,true))); // fan holds; tracks stop immediately
    quicker.reset();quicker.step(hand(1,100,0,.1f),100,true);
    assert(stopped(quicker.step(Target{},300,true)));
    Config bad_translation;bad_translation.pulse_ms=801;assert(!bad_translation.valid());
    bad_translation.pulse_ms=700;bad_translation.stale_ms=700;assert(!bad_translation.valid());
    auto absent=[](uint32_t id,int64_t time) { Target t; t.frame=id; t.captured_ms=time; return t; };
    HandFollower hold;
    assert(stopped(hold.step(absent(1,100),100,true)));
    assert(hold.step(hand(2,200,.8f),200,true).fan);
    assert(parked_fan(hold.step(absent(3,250),250,true))); // tracks stop, fan continues
    assert(hold.fan_hold_remaining_ms(250)==29950);
    assert(parked_fan(hold.step(absent(4,30199),30199,true)));
    assert(stopped(hold.step(absent(5,30200),30200,true))); // exact expiry
    hold.reset();
    hold.step(hand(1,100),100,true);
    hold.step(hand(2,20100),20100,true); // renewal grants another full 30 seconds
    assert(parked_fan(hold.step(absent(3,40000),40000,true)));
    assert(parked_fan(hold.step(absent(4,50099),50099,true)));
    assert(stopped(hold.step(absent(5,50100),50100,true)));
    hold.reset();hold.step(hand(1,100),100,true);
    hold.step(hand(1,100),900,true);
    assert(hold.fan_hold_remaining_ms(900)==29200); // duplicate frame doesn't extend
    assert(stopped(hold.step(absent(2,1000),2001,true))); // camera stalls override hold
    assert(hold.fan_hold_remaining_ms(2001)==0);
    assert(stopped(hold.step(absent(3,2100),2100,true))); // no revival after fault
    hold.step(hand(4,2200),2200,true);
    assert(stopped(hold.step(absent(5,2300),2300,false))); // stop clears hold
    assert(stopped(hold.step(absent(6,2400),2400,true)));
    Supervisor autonomous;
    assert(autonomous.arm(100,true));
    autonomous.tick(10000000); assert(autonomous.armed);
    assert(!autonomous.heartbeat(autonomous.session,10000001));
    autonomous.stop(); autonomous.tick(20000000); assert(!autonomous.armed);
    assert(!autonomous.heartbeat(autonomous.session,20000001));
    assert(autonomous.arm(20000002,true));
    HandFollower unattended;
    assert(stopped(unattended.step(Target{},20000003,autonomous.armed)));
    assert(unattended.step(hand(1,20000004),20000004,autonomous.armed).fan);
    assert(stopped(unattended.step(hand(1,20000004),20001005,autonomous.armed)));
    autonomous.stop("output_error"); assert(!autonomous.armed);
    Supervisor gate; assert(!gate.heartbeat(0,100)); assert(gate.arm(100));
    const auto old=gate.session; assert(!gate.arm(200)); assert(!gate.heartbeat(old+1,300));
    assert(gate.heartbeat(old,900)); gate.tick(1900); assert(!gate.armed);
    assert(!gate.heartbeat(old,2000)); assert(gate.arm(2000));
    assert(!gate.heartbeat(old,2100));
    for(int t=2200;t<32000;t+=200) assert(gate.heartbeat(gate.session,t));
    gate.tick(32000); assert(!gate.armed); // lease cannot extend session cap
    assert(gate.arm(33000)); gate.stop(); assert(!gate.heartbeat(gate.session,33001));
}
