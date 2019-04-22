import pandas as pd
import numpy as np

from settings import settings

num_augments = settings['NUM_AUGMENTS']

dataset = pd.read_csv(settings['SUBMISSIONS_PATH_FORMAT'] % num_augments)
dataset = dataset.set_index('object_id')

gal_classes = [6, 16, 53, 65, 92]
extgal_classes = [15, 42, 52, 62, 64, 67, 88, 90, 95]

gal_vals = dataset[['class_%d' % i for i in gal_classes]]
extgal_vals = dataset[['class_%d' % i for i in extgal_classes]]

gal_sum = np.sum(gal_vals, axis=1)
extgal_sum = np.sum(extgal_vals, axis=1)

is_gal = gal_sum > extgal_sum

# print("HACK: ADD IN CLASS WEIGHTS")
# dataset['class_64'] *= 2
# dataset['class_15'] *= 2

# Zero out cross-terms for galactic/extragalactic
for gal_class in gal_classes:
    dataset['class_%d' % gal_class][~is_gal] = 0
for extgal_class in extgal_classes:
    dataset['class_%d' % extgal_class][is_gal] = 0

# Remove class 99 predictions.
orig_99_preds = dataset['class_99'].copy()
dataset['class_99'] = 0.
norm = np.sum(dataset, axis=1)
dataset = dataset.div(norm, axis=0)

# Galactic predictions -> flat predictions
flat_pred = 0.04
dataset['class_99'][is_gal] = (flat_pred * norm) / (1 - flat_pred)
# dataset['class_99'][is_gal] = (orig_99_preds / norm)[is_gal]

pred_99_extgal = 0
c_vals = {
    '42': (1, 0.5),
    '62': (1, 0.3),
    '52': (1, 0.1),
    '95': (1, 0.1),
}

extgal_c_total = np.sum([i[1] for i in c_vals.values()])
print(extgal_c_total)
for label, (weight, c_val) in c_vals.items():
    frac_99 = c_val * 2 / weight / extgal_c_total
    pred_99_extgal += frac_99 * dataset['class_%s' % label]

dataset['class_99'][~is_gal] = pred_99_extgal[~is_gal]

# Normalize
dataset = dataset.div(np.sum(dataset, axis=1), axis=0)

dataset.to_csv(settings['SUBMISSIONS_PROBE99_PATH_FORMAT'] % num_augments)
