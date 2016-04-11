#   Copyright (c) 2016, Xilinx, Inc.
#   All rights reserved.
# 
#   Redistribution and use in source and binary forms, with or without 
#   modification, are permitted provided that the following conditions are met:
#
#   1.  Redistributions of source code must retain the above copyright notice, 
#       this list of conditions and the following disclaimer.
#
#   2.  Redistributions in binary form must reproduce the above copyright 
#       notice, this list of conditions and the following disclaimer in the 
#       documentation and/or other materials provided with the distribution.
#
#   3.  Neither the name of the copyright holder nor the names of its 
#       contributors may be used to endorse or promote products derived from 
#       this software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
#   THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
#   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
#   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#   OR BUSINESS INTERRUPTION). HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
#   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
#   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__author__      = "Cathal McCabe, Yun Rock Qu"
__copyright__   = "Copyright 2016, Xilinx"
__email__       = "xpp_support@xilinx.com"


import time
from . import _iop
from . import pmod_const
from pynq import MMIO

ALS_PROGRAM = "als.bin"
ALS_LOG_START = pmod_const.MAILBOX_OFFSET+16
ALS_LOG_END = ALS_LOG_START+(1000*4)

class ALS(object):
    """This class controls a light sensor PMOD.

    Attributes
    ----------
    iop : _IOP
        I/O processor instance used by ALS
    mmio : MMIO
        Memory-mapped I/O instance to read and write instructions and data.
    log_interval_ms : int
        Time in milliseconds between sampled reads of the ALS sensor
        
    """
    def __init__(self, pmod_id):
        """Return a new instance of an ALS object. 
        
        Parameters
        ----------
        pmod_id : int
            PMOD index in the programmable logic, starting at 1.
            
        """
        self.iop = _iop.request_iop(pmod_id, ALS_PROGRAM)
        self.mmio = self.iop.mmio
        self.log_interval_ms = 1000
        
        self.iop.start()
        
    def read(self):
        """Read current light value measured by the ALS PMOD.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        int
            The current sensor value.
        
        """
        self.mmio.write(pmod_const.MAILBOX_OFFSET+\
                        pmod_const.MAILBOX_PY2IOP_CMD_OFFSET, 3)      
        while (self.mmio.read(pmod_const.MAILBOX_OFFSET+\
                                pmod_const.MAILBOX_PY2IOP_CMD_OFFSET) == 3):
            pass
        return self.mmio.read(pmod_const.MAILBOX_OFFSET)

    def set_log_interval_ms(self,log_interval_ms):
        """Set the length of the log in the ALS PMOD.
        
        This method can set the length of the log, so that users can read out
        multiple values in a single log. 
        
        Parameters
        ----------
        log_interval_ms : int
            The length of the log in milliseconds, for debug only.
            
        Returns
        -------
        None
        
        """
        if (log_interval_ms < 0):
            raise ValueError("Log length should not be less than 0.")
        
        self.log_interval_ms = log_interval_ms
        self.mmio.write(pmod_const.MAILBOX_OFFSET+4, self.log_interval_ms)

    def start_log(self):
        """Start recording multiple values in a log.
        
        This method will first call set_log_interval_ms() before writting to
        the MMIO.
        
        Parameters
        ----------
        None
            
        Returns
        -------
        None
        
        """
        self.set_log_interval_ms(self.log_interval_ms)
        self.mmio.write(pmod_const.MAILBOX_OFFSET+\
                        pmod_const.MAILBOX_PY2IOP_CMD_OFFSET, 7)

    def stop_log(self):
        """Stop recording multiple values in a log.
        
        Simply write to the MMIO to stop the log.
        
        Parameters
        ----------
        None
            
        Returns
        -------
        None
        
        """
        self.mmio.write(pmod_const.MAILBOX_OFFSET+\
                        pmod_const.MAILBOX_PY2IOP_CMD_OFFSET, 1)    

    def get_log(self):
        """Return list of logged samples.
        
        Parameters
        ----------
        None
            
        Returns
        -------
        List of valid samples from the ALS sensor [0-255]
        
        """
        #: Stop logging
        self.stop_log()

        #: Prep iterators and results list
        head_ptr = self.mmio.read(pmod_const.MAILBOX_OFFSET+0x8)
        tail_ptr = self.mmio.read(pmod_const.MAILBOX_OFFSET+0xC)
        readings = list()

        #: Sweep circular buffer for samples
        if head_ptr == tail_ptr:
            return None
        elif head_ptr < tail_ptr:
            for i in range(head_ptr,tail_ptr,4):
                readings.append(self.mmio.read(i))
        else:
            for i in range(head_ptr,ALS_LOG_END,4):
                readings.append(self.mmio.read(i))
            for i in range(ALS_LOG_START,tail_ptr,4):            
                readings.append(self.mmio.read(i)) 

        return readings


     
