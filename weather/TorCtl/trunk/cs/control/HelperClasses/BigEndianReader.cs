/*
 * File BigEndianStream.cs
 * 
 * Copyright (C) 2005 Oliver Rau (olra0001@student-zw.fh-kl.de)
 * 
 * See LICENSE file for copying information 
 * 
 * Created on 19.09.2005 22:52
 * 
 * $Id: BigEndianReader.cs 6862 2005-11-09 21:47:04Z nickm $
 */

using System;
using System.IO;

namespace Tor.Control
{
	/// <summary>
	/// Implements a <see cref="BinaryReader">BinaryReader</see> which reads in big-endian order 
	/// instead of little-endian.
	/// </summary>
	/// <remarks>
	/// This class is not fully implemented, it's just implemented so far, that it will handle
	/// the operations needed by tor.<br />
	/// All the other operations are still the one's implemented by the <b>BinaryReader</b>.
	/// </remarks>
	public class BigEndianReader : BinaryReader
	{
		public BigEndianReader(Stream s) : base(s) {}
		
		new public ushort ReadUInt16()
		{
			byte high = base.ReadByte();
			byte low  = base.ReadByte();
			
			ushort result = Convert.ToUInt16(((high & 0xff) << 8) | (low & 0xffu));
			
			return result;
		}
	}
}
