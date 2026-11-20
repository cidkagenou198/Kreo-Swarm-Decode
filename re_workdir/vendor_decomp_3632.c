# Raw Ghidra 12.2 decompilation (language x86:LE:32:default:windows, no PDB available)
# Target: C:\Program Files (x86)\KreoSWARM75\OemDrv.exe
# Analysed copy: re_workdir\target\OemDrv.exe (byte-identical)
# SHA-256 ab0a2492c3538c247d4e6dfde1613cad5df78852490a41880a31fe47558b7117
# Verbatim tool output. Names inside log strings are the vendor's own.

# ------------------------------------------------------------------
# 0x00487fa0  SendCMD_3632  (log string: '!! SendCMD_3632: ...')
# ------------------------------------------------------------------
=== FUN_00487fa0 @ 00487fa0  size=693  completed=true ===

void __thiscall
FUN_00487fa0(int param_1,undefined1 param_2,uint param_3,int param_4,uint param_5,int param_6,
            int param_7)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  DWORD DVar4;
  uint uVar5;
  size_t _Size;
  wchar_t *pwVar6;
  uint local_34;
  int local_30;
  uint local_2c;
  int local_28;
  int local_24;
  int local_20;
  int local_1c;
  undefined1 local_18;
  byte bStack_17;
  byte bStack_16;
  byte bStack_15;
  undefined4 uStack_14;
  undefined4 uStack_10;
  undefined4 uStack_c;
  undefined1 uStack_8;
  undefined2 local_7;
  undefined1 local_5;
  uint local_4;
  
  local_4 = DAT_0063c674 ^ (uint)&local_34;
  local_1c = param_4;
  local_30 = param_1;
  if ((param_1 == 0) || (param_4 == 0)) {
    __security_check_cookie(local_4 ^ (uint)&local_34);
    return;
  }
  local_28 = param_7;
  local_20 = 5;
LAB_00487fe0:
  do {
    bStack_15 = 0;
    local_18 = param_2;
    _Size = 0;
    uStack_10 = 0;
    uStack_c = 0;
    uStack_8 = 0;
    local_7 = 0;
    local_5 = 0;
    bStack_17 = (byte)param_3;
    bStack_16 = 1;
    uStack_14 = 0;
    local_5 = FUN_00487cb0();
    iVar1 = FUN_00487e70(&local_18,1000);
    if (iVar1 == 0) {
      DVar4 = GetLastError();
      (*DAT_0064a278)(L"!! SendCMD_3632: send err=0x%x, cmd=0x%x",DVar4,param_3);
      __security_check_cookie(local_4 ^ (uint)&local_34);
      return;
    }
    local_24 = 0x14;
    local_2c = 0;
    uVar5 = 0;
    local_34 = 0;
    do {
      while( true ) {
        while( true ) {
          iVar1 = local_30;
          local_18 = 0;
          bStack_17 = 0;
          bStack_16 = 0;
          bStack_15 = 0;
          uStack_14 = 0;
          uStack_10 = 0;
          uStack_c = 0;
          uStack_8 = 0;
          local_7 = 0;
          local_5 = 0;
          iVar2 = FUN_00487d00(1000);
          if (iVar2 == 0) break;
          if (iVar2 == -2) {
            local_28 = local_28 + -1;
            if (local_28 < 1) {
              if (param_6 != 0) {
                (*DAT_0064a278)(L"!! SendCMD_3632: timeout, hDev=%x, cmd=0x%x, nPackages=%d, inx=%d, nCopys=%d"
                                ,iVar1,param_3,uVar5,local_34,_Size);
              }
              __security_check_cookie(local_4 ^ (uint)&local_34);
              return;
            }
            goto LAB_00487fe0;
          }
          if (iVar2 == -3) {
            (*DAT_0064a278)(L"!! SendCMD_3632: read err, hDev=%x, cmd=0x%x, nPackages=%d, inx=%d, nCopys=%d"
                            ,iVar1,param_3,uVar5,local_34,_Size);
            __security_check_cookie(local_4 ^ (uint)&local_34);
            return;
          }
        }
        local_34 = (uint)bStack_15;
        uVar3 = bStack_17 & 0x7f;
        uVar5 = bStack_16 & 0x7f;
        if ((param_3 & 0xff) == uVar3) break;
        local_24 = local_24 + -1;
        if (local_24 < 1) {
          pwVar6 = 
          L"SendCMD_3632: cmd unmatch for cmd=0x%x, nRetCmd=0x%x, package_index=%d, reread it";
          param_5 = local_34;
          goto LAB_004880c1;
        }
      }
      if ((char)bStack_17 < '\0') {
        (*DAT_0064a278)(L"SendCMD_3632: CRC check err for cmd=0x%x, redo it",param_3);
        goto LAB_00487fe0;
      }
      _Size = uStack_14 & 0xf;
      if ((int)param_5 < (int)_Size) {
        _Size = param_5;
      }
      else if (0xe < _Size) {
        _Size = 0xe;
      }
      uVar3 = local_2c + _Size;
      if ((int)uVar3 <= (int)param_5) {
        _memcpy((void *)(local_1c + local_2c),(void *)((int)&uStack_14 + 1),_Size);
      }
      local_2c = uVar3;
    } while (uVar5 != local_34 + 1);
    if ((int)param_5 <= (int)uVar3) {
      __security_check_cookie(local_4 ^ (uint)&local_34);
      return;
    }
    local_20 = local_20 + -1;
    if (local_20 < 1) {
      pwVar6 = L"SendCMD_3632: read length unmatch, cmd=0x%x, recvBytes=%d, nSize=%d";
LAB_004880c1:
      (*DAT_0064a278)(pwVar6,param_3,uVar3,param_5);
      __security_check_cookie(local_4 ^ (uint)&local_34);
      return;
    }
  } while( true );
}

# ------------------------------------------------------------------
# 0x00487d00  GetData_3632  (log string: 'GetData_3632 Err=0x%x')
# ------------------------------------------------------------------
=== FUN_00487d00 @ 00487d00  size=364  completed=true ===

void FUN_00487d00(DWORD param_1)

{
  BOOL BVar1;
  DWORD DVar2;
  HANDLE unaff_ESI;
  undefined4 *unaff_EDI;
  DWORD local_30;
  _OVERLAPPED local_2c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 local_10;
  undefined4 local_c;
  undefined4 local_8;
  uint local_4;
  
  local_4 = DAT_0063c674 ^ (uint)&local_30;
  local_2c.Internal = 0;
  local_2c.InternalHigh = 0;
  local_2c.u.s.Offset = 0;
  local_2c.u.s.OffsetHigh = 0;
  local_2c.hEvent = (HANDLE)0x0;
  local_2c.hEvent = CreateEventW((LPSECURITY_ATTRIBUTES)0x0,0,0,(LPCWSTR)0x0);
  local_30 = 0;
  local_18 = CONCAT31(local_18._1_3_,0x13);
  BVar1 = ReadFile(unaff_ESI,&local_18,0x14,&local_30,&local_2c);
  if (BVar1 == 0) {
    DVar2 = GetLastError();
    if (DVar2 == 0x3e5) {
      DVar2 = WaitForSingleObject(local_2c.hEvent,param_1);
      if (DVar2 == 0) {
        if (unaff_EDI != (undefined4 *)0x0) {
          *unaff_EDI = local_18;
          unaff_EDI[1] = local_14;
          unaff_EDI[2] = local_10;
          unaff_EDI[3] = local_c;
          unaff_EDI[4] = local_8;
        }
      }
      else if (DVar2 == 0x102) {
        BVar1 = CancelIo(unaff_ESI);
        if (BVar1 != 0) {
          GetOverlappedResult(unaff_ESI,&local_2c,&local_30,1);
        }
      }
      else {
        DVar2 = GetLastError();
        (*DAT_0064a278)(L"GetData_3632 Err=0x%x, hDev=%x",DVar2);
      }
    }
    else if (DVar2 == 0x48f) {
      (*DAT_0064a278)(L"GetData_3632 Err, dev is plugout, hDev=%x");
    }
    else {
      (*DAT_0064a278)(L"GetData_3632 Err=0x%x, hDev=%x",DVar2);
    }
  }
  else if (unaff_EDI != (undefined4 *)0x0) {
    *unaff_EDI = local_18;
    unaff_EDI[1] = local_14;
    unaff_EDI[2] = local_10;
    unaff_EDI[3] = local_c;
    unaff_EDI[4] = local_8;
  }
  CloseHandle(local_2c.hEvent);
  __security_check_cookie(local_4 ^ (uint)&local_30);
  return;
}

# ------------------------------------------------------------------
# 0x00487cb0  checksum helper (sum of all 20 bytes, byte 19 == 0)
# ------------------------------------------------------------------
=== FUN_00487cb0 @ 00487cb0  size=68  completed=true ===

char __fastcall FUN_00487cb0(int param_1)

{
  char cVar1;
  char *pcVar2;
  char cVar3;
  char cVar4;
  char cVar5;
  int iVar6;
  
  cVar4 = '\0';
  cVar1 = '\0';
  cVar3 = '\0';
  cVar5 = '\0';
  pcVar2 = (char *)(param_1 + 1);
  iVar6 = 5;
  do {
    cVar4 = cVar4 + *pcVar2;
    cVar1 = cVar1 + pcVar2[-1];
    cVar3 = cVar3 + pcVar2[2];
    cVar5 = cVar5 + pcVar2[1];
    pcVar2 = pcVar2 + 4;
    iVar6 = iVar6 + -1;
  } while (iVar6 != 0);
  return cVar1 + cVar3 + cVar5 + cVar4;
}

# ------------------------------------------------------------------
# 0x00487260  AccessData (multi-chunk write, 14 data bytes per packet)
# ------------------------------------------------------------------
=== FUN_00487260 @ 00487260  size=851  completed=true ===

void __thiscall
FUN_00487260(int param_1,int param_2,char param_3,int param_4,DWORD param_5,int param_6,
            undefined4 param_7)

{
  char cVar1;
  int iVar2;
  wchar_t *pwVar3;
  int iVar4;
  char cVar5;
  undefined1 auStack_38 [2];
  char local_36;
  char local_35;
  int local_34;
  byte local_2e;
  byte local_2d;
  size_t local_2c;
  int local_28;
  int local_24;
  int local_20;
  int local_1c;
  char local_18 [4];
  undefined4 local_14;
  undefined4 local_10;
  undefined4 local_c;
  undefined4 local_8;
  uint local_4;
  
  local_4 = DAT_0063c674 ^ (uint)auStack_38;
  iVar4 = *(int *)(param_1 + 0xc);
  if ((iVar4 == 0) || ((int)param_5 < 1)) {
    pwVar3 = L"CDev3632::AccessData param err, m_hDev=%x, nBytesToWrite=%d";
LAB_0048759a:
    (*DAT_0064a278)(pwVar3,iVar4,param_5);
  }
  else {
    *(undefined4 *)(param_1 + 0x24c) = 0;
    *(undefined4 *)(param_1 + 0x250) = 0;
    *(undefined4 *)(param_1 + 0x254) = 0;
    if (*(HANDLE *)(param_1 + 600) != (HANDLE)0x0) {
      ResetEvent(*(HANDLE *)(param_1 + 600));
    }
    local_20 = (int)param_5 / 0xe;
    local_28 = 0;
    if ((int)param_5 % 0xe != 0) {
      local_20 = local_20 + 1;
    }
    if ((int)param_5 < 1) {
LAB_0048753c:
      __security_check_cookie(local_4 ^ (uint)auStack_38);
      return;
    }
    local_2e = param_3 << 4;
    iVar4 = 0;
    while( true ) {
      local_2c = 0xe;
      if ((int)(param_5 - local_28) < 0xe) {
        local_2c = param_5 - local_28;
      }
      local_2d = local_2e | (byte)local_2c;
      local_24 = 0;
      while( true ) {
        FUN_00405170(param_7);
        local_10 = 0;
        local_c = 0;
        local_8 = 0;
        local_34 = iVar4 + 1;
        local_18[1] = (char)param_2;
        local_18[0] = 0x13;
        local_18[3] = (char)iVar4;
        local_18[2] = (undefined1)local_20;
        local_14 = (uint)local_2d;
        if (param_4 != 0) {
          _memcpy((void *)((int)&local_14 + 1),(void *)(local_28 + param_4),local_2c);
        }
        iVar4 = 0;
        cVar5 = '\0';
        local_36 = '\0';
        local_35 = '\0';
        cVar1 = '\0';
        do {
          local_36 = local_36 + local_18[iVar4 + 2];
          cVar5 = cVar5 + local_18[iVar4];
          cVar1 = cVar1 + local_18[iVar4 + 1];
          local_35 = local_35 + local_18[iVar4 + 3];
          iVar4 = iVar4 + 4;
        } while (iVar4 < 0x14);
        local_8 = CONCAT13(cVar1 + local_36 + local_35 + cVar5,(undefined3)local_8);
        iVar4 = param_2;
        if (*(int *)(param_1 + 0x238) == 0) {
          param_5 = local_34 - 1;
          pwVar3 = L"CDev3632::AccessData Online=0, cmd=0x%x, package=%d, return";
          goto LAB_0048759a;
        }
        iVar2 = FUN_00487e70(local_18,500);
        if (iVar2 == 0) {
          param_5 = GetLastError();
          pwVar3 = L"!! CDev3632::AccessData: send package %d err=0x%x";
          iVar4 = local_34 + -1;
          goto LAB_0048759a;
        }
        if (((char)param_2 < '\0') || (param_2 == 6)) goto LAB_004874d0;
        local_1c = -1;
        iVar2 = FUN_00486e20(param_2,(-(uint)(*(char *)(*(int *)(*(int *)(param_1 + 0x10) + 0x20) +
                                                       0x2d89) != '\0') & 5000) + 2000,local_18,
                             &local_1c);
        if (*(int *)(param_1 + 0x284) != 0) {
          (*DAT_0064a278)(L"CDev3632::AccessData: abort by user, cmd=0x%x",param_2);
          goto LAB_0048753c;
        }
        if (iVar2 == 0) break;
        if (iVar2 == -2) {
          if (*(int *)(param_1 + 0x238) == 0) {
            param_5 = local_34 - 1;
            pwVar3 = L"CDev3632::AccessData Online=0, cmd=0x%x, package=%d, no more retry, return";
            goto LAB_0048759a;
          }
        }
        else if (iVar2 != -3) {
          (*DAT_0064a278)(L"!! CDev3632::AccessData: read err, cmd=0x%x, nRet=%d, package=%d",
                          param_2,iVar2,local_34 + -1);
          goto LAB_004875a3;
        }
        if ((param_6 == 0) || (4 < local_24)) {
          pwVar3 = L"timeout";
          if (iVar2 != -2) {
            pwVar3 = L"crc";
          }
          (*DAT_0064a278)(L"!! CDev3632::AccessData: %s err, cmd=0x%x, package=%d",pwVar3,param_2,
                          local_34 + -1);
          goto LAB_004875a3;
        }
        local_24 = local_24 + 1;
        iVar4 = local_34 + -1;
      }
      if (local_1c != local_34 + -1) break;
LAB_004874d0:
      local_28 = local_28 + local_2c;
      if ((int)param_5 <= local_28) {
        __security_check_cookie(local_4 ^ (uint)auStack_38);
        return;
      }
      iVar4 = local_34;
    }
    (*DAT_0064a278)(L"!! CDev3632::AccessData: package index err, cmd=0x%x, send=0x%x, in=0x%x",
                    param_2,local_34 + -1,local_1c);
  }
LAB_004875a3:
  __security_check_cookie(local_4 ^ (uint)auStack_38);
  return;
}

# ------------------------------------------------------------------
# 0x004875c0  SendCMD (single packet + chunked response assemble)
# ------------------------------------------------------------------
=== FUN_004875c0 @ 004875c0  size=702  completed=true ===

void __thiscall FUN_004875c0(int param_1,undefined4 param_2,char param_3,int param_4,size_t param_5)

{
  int iVar1;
  DWORD DVar2;
  uint uVar3;
  size_t _Size;
  wchar_t *pwVar4;
  undefined4 uVar5;
  undefined1 auStack_34 [3];
  byte local_31;
  uint local_30;
  int local_2c;
  int local_28;
  int local_24;
  int local_20;
  int local_1c;
  undefined1 local_18;
  undefined1 uStack_17;
  byte bStack_16;
  byte bStack_15;
  undefined4 uStack_14;
  undefined4 uStack_10;
  undefined4 uStack_c;
  undefined1 uStack_8;
  undefined2 local_7;
  undefined1 local_5;
  uint local_4;
  
  local_4 = DAT_0063c674 ^ (uint)auStack_34;
  local_1c = param_4;
  if ((*(int *)(param_1 + 0xc) != 0) && (param_4 != 0)) {
    if (*(int *)(param_1 + 0x238) != 0) {
      *(undefined4 *)(param_1 + 0x24c) = 0;
      *(undefined4 *)(param_1 + 0x250) = 0;
      *(undefined4 *)(param_1 + 0x254) = 0;
      if (*(HANDLE *)(param_1 + 600) != (HANDLE)0x0) {
        ResetEvent(*(HANDLE *)(param_1 + 600));
      }
      local_31 = param_3 << 4;
      local_2c = 0;
LAB_00487650:
      do {
        uVar3 = 0;
        bStack_15 = 0;
        uStack_14 = (uint)local_31;
        uStack_10 = 0;
        uStack_c = 0;
        uStack_8 = 0;
        local_7 = 0;
        local_5 = 0;
        local_18 = 0x13;
        uStack_17 = (undefined1)param_2;
        bStack_16 = 1;
        local_5 = FUN_00487cb0();
        iVar1 = FUN_00487e70(&local_18,500);
        if (iVar1 == 0) {
          DVar2 = GetLastError();
          (*DAT_0064a278)(L"!!CDev3632::SendCMD: send err=0x%x, cmd=0x%x",DVar2,param_2);
LAB_004877d1:
          __security_check_cookie(local_4 ^ (uint)auStack_34);
          return;
        }
        _Size = 0;
        local_28 = 0;
        local_30 = 0;
        local_24 = -1;
LAB_004876c1:
        do {
          local_18 = 0;
          uStack_17 = 0;
          bStack_16 = 0;
          bStack_15 = 0;
          uStack_14 = 0;
          uStack_10 = 0;
          uStack_c = 0;
          uStack_8 = 0;
          local_7 = 0;
          local_5 = 0;
          local_20 = -1;
          iVar1 = FUN_00486e20(param_2,(-(uint)(*(char *)(*(int *)(*(int *)(param_1 + 0x10) + 0x20)
                                                         + 0x2d89) != '\0') & 5000) + 2000,&local_18
                               ,&local_20);
          if (*(int *)(param_1 + 0x284) != 0) {
            (*DAT_0064a278)(L"CDev3632::SendCMD: abort by user, cmd=0x%x",param_2);
            goto LAB_00487835;
          }
          if (iVar1 != 0) {
            if (iVar1 == -2) {
              if (*(int *)(param_1 + 0x238) == 0) {
                (*DAT_0064a278)(L"CDev3632::SendCMD Online=0, cmd=0x%x, inx=%d, no more retry, return"
                                ,param_2,local_30);
                goto LAB_004877d1;
              }
              if (local_2c < 5) {
                local_2c = local_2c + 1;
                goto LAB_00487650;
              }
              uVar5 = *(undefined4 *)(param_1 + 0xc);
              pwVar4 = 
              L"!!CDev3632::SendCMD: timeout, hDev=%x, cmd=0x%x, nPackages=%d, inx=%d, nCopys=%d";
            }
            else {
              if (iVar1 != -4) goto LAB_004876c1;
              uVar5 = *(undefined4 *)(param_1 + 0xc);
              pwVar4 = 
              L"!!CDev3632::SendCMD: read err, hDev=%x, cmd=0x%x, nPackages=%d, inx=%d, nCopys=%d";
            }
            (*DAT_0064a278)(pwVar4,uVar5,param_2,uVar3,local_30,_Size);
            goto LAB_004877d1;
          }
          if (local_20 == local_24) {
            (*DAT_0064a278)(L"CDev3632::SendCMD: get repeat package index, cmd=0x%x, index=%d, ignore it"
                            ,param_2,local_20);
            goto LAB_004876c1;
          }
          local_30 = (uint)bStack_15;
          local_24 = local_20;
          _Size = uStack_14 & 0xf;
          uVar3 = bStack_16 & 0x7f;
          if ((int)param_5 < (int)_Size) {
            _Size = param_5;
          }
          else if (0xe < _Size) {
            _Size = 0xe;
          }
          iVar1 = _Size + local_28;
          if (iVar1 <= (int)param_5) {
            _memcpy((void *)(local_1c + local_28),(void *)((int)&uStack_14 + 1),_Size);
          }
          local_28 = iVar1;
        } while (uVar3 != local_30 + 1);
        if ((int)param_5 <= iVar1) {
LAB_00487835:
          __security_check_cookie(local_4 ^ (uint)auStack_34);
          return;
        }
      } while( true );
    }
    (*DAT_0064a278)(L"CDev3632::SendCMD Online=0, cmd=0x%x, return",param_2);
  }
  __security_check_cookie(local_4 ^ (uint)auStack_34);
  return;
}
