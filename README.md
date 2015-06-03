chlib
=====

***NOTE*** This library is now maintained by piks and sorch, any issues regarding chlib can be redirected to one of these two.

A chatango library with a flexable manager - Stable channel.

Requirements: This library requires at this time to have python 3 or greater installed.

TOS: You may not use this library to explicitely run ANY code that was not created from the original user OR ported from any previous bot using the ch.py library (including any derivative) UNLESS you made any code that ran on ch.py FROM YOUR EXISTING KNOWLEDGE.

License: MIT

Methods and parameters (outdated):

groups:

The group method's are now based on the command chatango send's. recvOldMethodName(args) = recvNewMethodName(args)

recvFailedLogin(group) = recvdenied(group)

recvInit(group) = recvinited(group)

recvUserLeave(group, user) = recvparticipant(bit, group, user, uid) NOTE: bit = 0

recvUserJoin(group, user) = recvparticipant(bit, group, user, uid) NOTE: bit = 1

recvCommand(user, group, auth, post, command, command arguments) NOTE: unchanged

recvPost(user, group, auth, post) NOTE: unchanged

recvModErase(group, user) = recvmods(added, group, mod) NOTE: added = false

recvModAdd(group, user) = recvmods(added, group, mod) NOTE: added = true

recvPostDelete(group, post) = recvdelete(group, post)

recvBan(group, user, mod) = recvblocked(group, user, mod)

recvUnban(group, user, mod) = recvunblocked(group, user mod)

recvLogout(group) = recvlogoutok(group)

recvLogin(group) = recvpwdok(group)

recvGroupClear(group) = recvclearall(group)

recvFlWarning(group) = recvshow_fw(group)

recvGroupBan(group) = recvshow_tb(group, mins, secs)

recvGroupBanUpdate(minutes, seconds) = recvtb(group, mins, secs)

PM's:

recvPMInit(group) = recvOK(group)

recvOfflinePM(user, pm) = recvmsgoff(user, pm)

recvPm(user, pm) = recvmsg(user, pm)

recvPMKick() = recvkickingoff(group)
