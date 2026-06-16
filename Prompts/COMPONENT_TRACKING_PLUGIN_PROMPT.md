## OPERATIONAL MEMORY & CONDITION ASSESSMENT

### Core Principle

The system must improve automatically through normal operational activity.

It must never depend on users performing ongoing manual maintenance to remain accurate.

Manual data entry should only be used to seed the system where historical information does not exist.

---

## INITIAL CONDITION ASSESSMENT

For existing installations where no installation history exists:

Authorised personnel (typically Team Leaders or Engineering Admin) may perform a one-time Condition Assessment.

Possible values:

* Unknown
* New
* Good
* Fair
* Poor
* Critical

Optional fields:

* Estimated Age
* Estimated Remaining Life
* Confidence Level
* Notes
* Assessed By
* Assessment Date

This assessment is only intended to initialise the system.

Once a verified replacement occurs, actual history becomes the authoritative source.

---

## COMPONENT HEARTBEAT

Every component may have an Operational Heartbeat.

Heartbeat Start:

* Verified installation
* Verified replacement
* Verified commissioning

Heartbeat Reset:

* Every confirmed replacement event

Heartbeat Data:

* Installation Date
* Running Age
* Replacement Count
* Failure Count
* Last Replacement
* Last Failure
* Lifetime History

Heartbeat updates must occur automatically as a by-product of normal work order completion.

No separate maintenance process should be required.

---

## UNKNOWN COMPONENTS

The system must never force users to guess.

If age, condition or installation date cannot be determined:

Status:

* Unknown

This is an acceptable and valid state.

Unknown values should not prevent system operation.

---

## NON-WEAR COMPONENTS

Certain components may not have meaningful age-based health tracking.

Examples:

* Covers
* Plates
* Guards
* Brackets
* Structural Items
* Labels
* Frames

These components should support:

* Unknown Lifetime
* Optional Condition Assessment
* Replacement History

If they are ever replaced, the replacement event must still be recorded and their Operational Heartbeat must begin from that date.

The system should not force estimated ages or artificial health values where they provide no engineering value.

---

## PASSIVE LEARNING PRINCIPLE

The software should continuously learn from:

* Purchase Orders
* Goods Received
* Stock Issues
* Work Orders
* Part Replacements
* Failure Reports
* Supplier Information
* Engineering Drawings
* Spare Parts Lists

Users should improve the database simply by doing their normal jobs.

The objective is Zero-Maintenance Intelligence.

The software should become more accurate every year without requiring dedicated data-capture projects.
