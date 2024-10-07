# Change Log
All notable changes to this project will be documented in this file.

## 1.2.1 - 2024-09-24

### Fixed
- The way the program takes in a list for the cap probe signal (axes) was affecting jitter and min step tests that only used the encoder. I differentiated between rotary and linear stages and how they handle taking in probe axis (axes.

## 1.2.0 - 2024-09-24

### Added
- Functionality take in data from two cap probes for min step/jitter on rotary stages.

## 1.1.0 - 2024-09-24

### Added
- Functionality to report units in microradians for the Jitter and Min Step tests.

## 1.0.1 - 2024-09-16

### Fixed
- Fixed embedded plot formatting issues when run from a .bat file.

## 1.0.0 - 2024-09-06

### Added
- Rewrote all .py files to work with a Production facing UI
- Added a readme and a changelog

## 0.0.0 - 2024-09-01

### Added
- Initial commit
