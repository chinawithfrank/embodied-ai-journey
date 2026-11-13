#include <cassert>
#include <limits>
#include "autonomy/controller.hpp"
using namespace robot;
static Target hand(uint32_t frame, int64_t time, float x=0, float size=.35f) {
    Target t; t.valid=true; t.frame=frame; t.captured_ms=time; t.x=x; t.size=size; return t;
}
static bool stopped(Command c) { return !c.left && !c.right && !c.fan; }
int main() {
    Config legacy; legacy.turn_min_ms=legacy.turn_max_ms=100; legacy.turn_cooldown_ms=300;
    HandFollower f(legacy);
    assert(stopped(f.step(hand(1,100),100,false)));
    auto c=f.step(hand(1,100,.6f),100,true);
    assert(c.left>0 && c.right<0 && !c.fan);
    assert(stopped(f.step(hand(1,100,.6f),200,true))); // independent pulse expiry
    assert(stopped(f.step(hand(1,100,.6f),600,true))); // no repeated-frame pulse
    c=f.step(hand(2,600,-.6f),600,true); assert(c.left<0 && c.right>0);
    c=f.step(hand(3,650,-.6f),650,true); assert(c.left<0); // finish existing pulse
    assert(stopped(f.step(hand(3,650,-.6f),700,true)));
    c=f.step(hand(4,1100,0,.15f),1100,true); assert(c.left>0 && c.right>0);
    c=f.step(hand(5,1600,0,.6f),1600,true); assert(c.left<0 && c.right<0);
    assert(stopped(f.step(hand(6,2100),2100,true)));
    assert(stopped(f.step(hand(6,2100),2150,true)));
    assert(stopped(f.step(hand(7,2500),2500,true)));
    c=f.step(hand(8,2900),2900,true); assert(c.fan && !c.left && !c.right);
    c=f.step(hand(9,3300,.16f,.40f),3300,true); assert(c.fan); // hysteresis
    assert(stopped(f.step(hand(9,3300),4301,true))); // inference stalled
    assert(stopped(f.step(Target{},4400,true)));
    f.reset(); auto high=hand(1,100); high.y=.7f; assert(stopped(f.step(high,100,true)));
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
    assert(stopped(adaptive.step(hand(3,300,.7f),450,true))); // original 350ms cap
    assert(stopped(adaptive.step(hand(4,500,.7f),500,true))); // cooldown
    c=adaptive.step(hand(5,600,.7f),600,true); assert(c.left>0);
    assert(stopped(adaptive.step(hand(6,650,-.7f),650,true))); // crossing stops, no instant reverse
    adaptive.reset();
    c=adaptive.step(hand(1,100,.13f),100,true); assert(c.left>0);
    assert(stopped(adaptive.step(hand(1,100,.13f),205,true))); // near centre: about 103ms
    adaptive.reset();
    adaptive.step(hand(1,100,1),100,true);
    assert(stopped(adaptive.step(hand(2,200,0),200,true))); // stop early when centred
    adaptive.reset();
    adaptive.step(hand(1,100,1),100,true);
    assert(stopped(adaptive.step(Target{},150,true))); // lost target interrupts long pulse
    Config bad_turn; bad_turn.turn_max_ms=401; assert(!bad_turn.valid());
    bad_turn.turn_max_ms=350; bad_turn.stale_ms=300; assert(!bad_turn.valid());
    Supervisor gate; assert(!gate.heartbeat(0,100)); assert(gate.arm(100));
    const auto old=gate.session; assert(!gate.arm(200)); assert(!gate.heartbeat(old+1,300));
    assert(gate.heartbeat(old,900)); gate.tick(1900); assert(!gate.armed);
    assert(!gate.heartbeat(old,2000)); assert(gate.arm(2000));
    assert(!gate.heartbeat(old,2100));
    for(int t=2200;t<32000;t+=200) assert(gate.heartbeat(gate.session,t));
    gate.tick(32000); assert(!gate.armed); // lease cannot extend session cap
    assert(gate.arm(33000)); gate.stop(); assert(!gate.heartbeat(gate.session,33001));
}
