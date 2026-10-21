"""Cek level logger app.ai TANPA basicConfig buatan — liar(0)=ikut root."""
import logging

from app import ai

print('logger   :', ai.log.name)
print('eff      :', ai.log.getEffectiveLevel(), '(20=INFO, 30=WARNING, 0=NOTSET->root)')
print('parent   :', ai.log.parent.name, ai.log.parent.getEffectiveLevel())
print('root eff :', logging.getLogger().getEffectiveLevel())
print('root hdl :', logging.getLogger().handlers)
print('propagate:', ai.log.propagate)