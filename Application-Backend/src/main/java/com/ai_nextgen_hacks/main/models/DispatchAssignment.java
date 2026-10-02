package com.ai_nextgen_hacks.main.models;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "dispatch_assignments")
public class DispatchAssignment {
    @Id
    private String orderId;
    private String unitId;
    private LocalDateTime assignedAt;
    private LocalDateTime plannedDeparture;
    private String status;

    public DispatchAssignment() {}

    public String getOrderId() { return orderId; }
    public void setOrderId(String orderId) { this.orderId = orderId; }

    public String getUnitId() { return unitId; }
    public void setUnitId(String unitId) { this.unitId = unitId; }

    public LocalDateTime getAssignedAt() { return assignedAt; }
    public void setAssignedAt(LocalDateTime assignedAt) { this.assignedAt = assignedAt; }

    public LocalDateTime getPlannedDeparture() { return plannedDeparture; }
    public void setPlannedDeparture(LocalDateTime plannedDeparture) { this.plannedDeparture = plannedDeparture; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
