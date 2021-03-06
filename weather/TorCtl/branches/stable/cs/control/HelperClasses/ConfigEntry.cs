/*
 * File ConfigEntry.cs
 * 
 * Copyright (C) 2005 Oliver Rau (olra0001@student-zw.fh-kl.de)
 * 
 * See LICENSE file for copying information 
 * 
 * Created on 08.08.2005 20:37
 * 
 * $Id: ConfigEntry.cs 6862 2005-11-09 21:47:04Z nickm $
 */

using System;

namespace Tor.Control
{
	/// <summary>
	/// Description of ConfigEntry.
	/// </summary>
	public class ConfigEntry
	{
		string key;
		string value;
		
		#region Getter Methods
		public string Key {
			get {
				return key;
			}
		}
		public string Value {
			get {
				return value;
			}
		}
		#endregion Getter Methods
		
		public ConfigEntry(string k, string v)
		{
			key   = k;
			value = v;
		}
	}
}
