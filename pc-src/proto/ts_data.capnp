@0xf26b1dda31dcde85;

struct TSData {
    isEmergency @0 :Bool;
    isEmergencyButtonPressed @1 :Bool;
    isEmergencySwitchToggled @2 :Bool;
    isHydrogenLeaking @3 :Bool;
    isScRelayClosed @4 :Bool;
    isTimeResetButtonPressed @5 :Bool;
    isHalfSpeedButtonPressed @6 :Bool;
    isGasButtonPressed @7 :Bool;
    fuelCellMode @8 :FuelCellMode;

    fcCurrent @9 :Float32;
    fcScCurrent @10 :Float32;
    scMotorCurrent @11 :Float32;
    fcVoltage @12 :Float32;
    scVoltage @13 :Float32;
    hydrogenSensorVoltage @14 :Float32;
    fuelCellTemperature @15 :Float32;
    fanRpm @16 :Int32;
    vehicleSpeed @17 :Float32;
    motorPwm @18 :Int32;
    hydrogenPressure @19 :Float32;

    gpsLatitude @20 :Float32;
    gpsLongitude @21 :Float32;
    gpsAltitude @22 :Float32;
    gpsSpeed @23 :Float32;

    motorSpeed @24 :Float32;
    motorCurrent @25 :Float32;
    fcCurrentRaw @26 :Float32;
    fcVoltageRaw @27 :Float32;
    mcCurrent @28 :Float32;

    lapNumber @29 :UInt8;

    enum FuelCellMode {
    	noneSelected @0;
    	off @1;
    	prepareToRace @2;
    	race @3;
    }
    
}