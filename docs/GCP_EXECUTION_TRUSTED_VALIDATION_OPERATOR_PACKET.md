# GCP Execution Trusted Validation Operator Packet

This packet is the top-level operator checklist for the first sanctioned broker-facing VM validation session.

## Goal

Reduce the first trusted validation session to one governed sequence:

1. arm a bounded exclusive window
2. launch the VM session
3. run post-session assimilation
4. close the exclusive window
5. review the refreshed evidence packets

## Why This Exists

The project already has:

- an exclusive-window packet
- a trusted-validation readiness packet
- a trusted launch pack
- a closeout packet

The remaining risk is operator error across those packets. This packet stitches them into one controlled flow.

## Preferred Entrypoint

- `cleanroom/code/qqq_options_30d_cleanroom/build_gcp_execution_trusted_validation_operator_packet.py`

## Expected States

- before arming: operator packet should say `ready_to_arm_window`
- after arming: operator packet should move toward launch readiness after the underlying packets refresh
- after the session: closeout should be run immediately and the packet should no longer imply an open window

## Rules

- do not arm the window unless the paper account is actually available
- do not start the VM session until the refreshed launch pack says `ready_to_launch`
- do not skip post-session assimilation
- do not leave the exclusive window armed after the session ends
