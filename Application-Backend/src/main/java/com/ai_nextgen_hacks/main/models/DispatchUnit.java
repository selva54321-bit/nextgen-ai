package com.ai_nextgen_hacks.main.models;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "dispatch_units")
public class DispatchUnit {
    @Id
    private String unitId;
    private Double capacity;
    private String availability; // e.g., AVAILABLE, BUSY, OFFLINE
    private String currentLocation;

    public DispatchUnit() {}

    public String getUnitId() { return unitId; }
    public void setUnitId(String unitId) { this.unitId = unitId; }

    public Double getCapacity() { return capacity; }
    public void setCapacity(Double capacity) { this.capacity = capacity; }

    public String getAvailability() { return availability; }
    public void setAvailability(String availability) { this.availability = availability; }

    public String getCurrentLocation() { return currentLocation; }
    public void setCurrentLocation(String currentLocation) { this.currentLocation = currentLocation; }
}
