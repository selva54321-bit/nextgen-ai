package com.ai_nextgen_hacks.main.models;

import java.util.UUID;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;

@Entity
public class ShipmentData
{
	@Id
	@GeneratedValue(strategy=GenerationType.AUTO)
	private UUID id;

}
