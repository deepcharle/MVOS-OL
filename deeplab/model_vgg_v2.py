import torch.nn as nn
import torch
import numpy as np
from collections import OrderedDict
from deeplab.layers import *

## Functional definitions for model 
## Useful for when weights are exposed rather than being contained in modules
def fun_conv1_features(x, weights):
    # conv 1
    x = conv2d(x, weights['conv_1.0.weight'], weights['conv_1.0.bias'], stride=1, padding=1)
    x = relu(x)
    x = conv2d(x, weights['conv_1.2.weight'], weights['conv_1.2.bias'], stride=1, padding=1)
    x = relu(x)
    x = maxpool(x, kernel_size=3, stride=2, padding=1)
    return x

def fun_conv2_features(x, weights):
    # conv 2
    x = conv2d(x, weights['conv_2.0.weight'], weights['conv_2.0.bias'], stride=1, padding=1)
    x = relu(x)
    x = conv2d(x, weights['conv_2.2.weight'], weights['conv_2.2.bias'], stride=1, padding=1)
    x = relu(x)
    x = maxpool(x, kernel_size=3, stride=2, padding=1)
    return x

def fun_conv3_features(x, weights):
    # conv 3
    x = conv2d(x, weights['conv_3.0.weight'], weights['conv_3.0.bias'], stride=1, padding=1)
    x = relu(x)
    x = conv2d(x, weights['conv_3.2.weight'], weights['conv_3.2.bias'], stride=1, padding=1)
    x = relu(x)
    x = conv2d(x, weights['conv_3.4.weight'], weights['conv_3.4.bias'], stride=1, padding=1)
    x = relu(x)
    x = maxpool(x, kernel_size=3, stride=2, padding=1)
    return x

def fun_conv4_features(x, weights):
    # conv 4
    x = conv2d(x, weights['conv_4.0.weight'], weights['conv_4.0.bias'], stride=1, padding=1)
    x = relu(x)
    x = conv2d(x, weights['conv_4.2.weight'], weights['conv_4.2.bias'], stride=1, padding=1)
    x = relu(x)
    x = conv2d(x, weights['conv_4.4.weight'], weights['conv_4.4.bias'], stride=1, padding=1)
    x = relu(x)
    x = maxpool(x, kernel_size=3, stride=1, padding=1)
    return x

def fun_conv5_features(x, weights):
    # conv 5
    x = conv2d(x, weights['conv_5.0.weight'], weights['conv_5.0.bias'], stride=1, padding=2, dilation=2)
    x = relu(x)
    x = conv2d(x, weights['conv_5.2.weight'], weights['conv_5.2.bias'], stride=1, padding=2, dilation=2)
    x = relu(x)
    x = conv2d(x, weights['conv_5.4.weight'], weights['conv_5.4.bias'], stride=1, padding=2, dilation=2)
    x = relu(x)
    x = maxpool(x, kernel_size=3, stride=1, padding=1)
    return x

def fun_deeplab_assp(x, weights, is_train=True):
    # Assp branch 1
    x1 = conv2d(x, weights['assp_1.conv.features.0.weight'], weights['assp_1.conv.features.0.bias'], stride=1, padding=6, dilation=6)
    x1 = relu(x1)
    x1 = dropout(x1, is_train)
    x1 = conv2d(x1, weights['assp_1.conv.features.3.weight'], weights['assp_1.conv.features.3.bias'], stride=1, padding=0)
    x1 = relu(x1)
    x1 = dropout(x1, is_train)
    x1 = conv2d(x1, weights['assp_1.pred.weight'], weights['assp_1.pred.bias'], stride=1, padding=0)

    # Assp branch 2
    x2 = conv2d(x, weights['assp_2.conv.features.0.weight'], weights['assp_2.conv.features.0.bias'], stride=1, padding=12, dilation=12)
    x2 = relu(x2)
    x2 = dropout(x2, is_train)
    x2 = conv2d(x2, weights['assp_2.conv.features.3.weight'], weights['assp_2.conv.features.3.bias'], stride=1, padding=0)
    x2 = relu(x2)
    x2 = dropout(x2, is_train)
    x2 = conv2d(x2, weights['assp_2.pred.weight'], weights['assp_2.pred.bias'], stride=1, padding=0)

    # Assp branch 3
    x3 = conv2d(x, weights['assp_3.conv.features.0.weight'], weights['assp_3.conv.features.0.bias'], stride=1, padding=18, dilation=18)
    x3 = relu(x3)
    x3 = dropout(x3, is_train)
    x3 = conv2d(x3, weights['assp_3.conv.features.3.weight'], weights['assp_3.conv.features.3.bias'], stride=1, padding=0)
    x3 = relu(x3)
    x3 = dropout(x3, is_train)
    x3 = conv2d(x3, weights['assp_3.pred.weight'], weights['assp_3.pred.bias'], stride=1, padding=0)

    # Assp branch 4
    x4 = conv2d(x, weights['assp_4.conv.features.0.weight'], weights['assp_4.conv.features.0.bias'], stride=1, padding=24, dilation=24)
    x4 = relu(x4)
    x4 = dropout(x4, is_train)
    x4 = conv2d(x4, weights['assp_4.conv.features.3.weight'], weights['assp_4.conv.features.3.bias'], stride=1, padding=0)
    x4 = relu(x4)
    x4 = dropout(x4, is_train)
    x4 = conv2d(x4, weights['assp_4.pred.weight'], weights['assp_4.pred.bias'], stride=1, padding=0)

    return x1 + x2 + x3 + x4

## VGG16-based deeplab v2
def make_vgg_layers(network_cfg, in_channels=3, dilation=1):
    layers = []

    for v in network_cfg:
        if v == 'M1':
            layers += [nn.MaxPool2d(kernel_size=3, stride=1, padding=1)]
        elif v == 'M2':
            layers += [nn.MaxPool2d(kernel_size=3, stride=2, padding=1)]
        else:
            conv2d = nn.Conv2d(in_channels, v, kernel_size=3, padding=dilation, dilation=dilation)
            layers += [conv2d, nn.ReLU(inplace=True)]
            in_channels = v
    return nn.Sequential(*layers)

class Assp_Branch(nn.Module):

    def __init__(self, dilation, in_features=512):
        super(Assp_Branch, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_features, 1024, kernel_size=3, stride=1, padding=dilation, dilation=dilation),
            nn.ReLU(inplace=True),
            nn.Dropout(),
            nn.Conv2d(1024, 1024, kernel_size=1, stride=1),
            nn.ReLU(inplace=True),
            nn.Dropout(),
            )

    def forward(self, x):
        return self.features(x)


class Vgg_Seg(nn.Module):

    def __init__(self, num_classes):
        super(Vgg_Seg, self).__init__()
        self.conv_1 = make_vgg_layers([64, 64, 'M2'], in_channels=3)
        self.conv_2 = make_vgg_layers([128, 128, 'M2'], in_channels=64)
        self.conv_3 = make_vgg_layers([256, 256, 256, 'M2'], in_channels=128)
        self.conv_4 = make_vgg_layers([512, 512, 512, 'M1'], in_channels=256)
        self.conv_5 = make_vgg_layers([512, 512, 512, 'M1'], in_channels=512, dilation=2)

        self.assp_1 = nn.Sequential(OrderedDict([
            ('conv', Assp_Branch(6)),
            ('pred', nn.Conv2d(1024, num_classes, kernel_size=1, stride=1)),
        ]))

        self.assp_2 = nn.Sequential(OrderedDict([
            ('conv', Assp_Branch(12)),
            ('pred', nn.Conv2d(1024, num_classes, kernel_size=1, stride=1)),
        ]))

        self.assp_3 = nn.Sequential(OrderedDict([
            ('conv', Assp_Branch(18)),
            ('pred', nn.Conv2d(1024, num_classes, kernel_size=1, stride=1)),
        ]))

        self.assp_4 = nn.Sequential(OrderedDict([
            ('conv', Assp_Branch(24)),
            ('pred', nn.Conv2d(1024, num_classes, kernel_size=1, stride=1)),
        ]))

        layer_count = 0
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()
                layer_count += 1
        print ('Initialize {} Conv2d layers...'.format(layer_count))

    def forward(self, x):
        x = self.conv_1(x)
        x = self.conv_2(x)
        x = self.conv_3(x)
        x = self.conv_4(x)
        x = self.conv_5(x)
        x = self.assp_1(x) + self.assp_2(x) + self.assp_3(x) + self.assp_4(x)
        return x

class Vgg_Meta_Seg(nn.Module):
    def __init__(self, num_classes):
        super(Vgg_Meta_Seg, self).__init__()
        self.conv_1 = make_vgg_layers([64, 64, 'M2'], in_channels=3)
        self.conv_2 = make_vgg_layers([128, 128, 'M2'], in_channels=64)
        self.conv_3 = make_vgg_layers([256, 256, 256, 'M2'], in_channels=128)
        self.conv_4 = make_vgg_layers([512, 512, 512, 'M1'], in_channels=256)
        self.conv_5 = make_vgg_layers([512, 512, 512, 'M1'], in_channels=512, dilation=2)

        self.assp_1 = nn.Sequential(OrderedDict([
            ('conv', Assp_Branch(6)),
            ('pred', nn.Conv2d(1024, num_classes, kernel_size=1, stride=1)),
        ]))

        self.assp_2 = nn.Sequential(OrderedDict([
            ('conv', Assp_Branch(12)),
            ('pred', nn.Conv2d(1024, num_classes, kernel_size=1, stride=1)),
        ]))

        self.assp_3 = nn.Sequential(OrderedDict([
            ('conv', Assp_Branch(18)),
            ('pred', nn.Conv2d(1024, num_classes, kernel_size=1, stride=1)),
        ]))

        self.assp_4 = nn.Sequential(OrderedDict([
            ('conv', Assp_Branch(24)),
            ('pred', nn.Conv2d(1024, num_classes, kernel_size=1, stride=1)),
        ]))

    def forward(self, x, weights=None, train_mode=None, is_train=True):
        if weights == None:
            x = self.conv_1(x)
            x = self.conv_2(x)
            x = self.conv_3(x)
            x = self.conv_4(x)
            x = self.conv_5(x)
            x = self.assp_1(x) + self.assp_2(x) + self.assp_3(x) + self.assp_4(x)
        else:
            if train_mode == None:
                x = self.conv_1(x)
                x = self.conv_2(x)
                x = self.conv_3(x)
                x = self.conv_4(x)
                x = self.conv_5(x)
            elif train_mode == 'conv_3_4_5':
                x = self.conv_1(x)
                x = self.conv_2(x)
                x = fun_conv3_features(x, weights)
                x = fun_conv4_features(x, weights)
                x = fun_conv5_features(x, weights)
            elif train_mode == 'conv_4_5':
                x = self.conv_1(x)
                x = self.conv_2(x)
                x = self.conv_3(x)
                x = fun_conv4_features(x, weights)
                x = fun_conv5_features(x, weights)
            elif train_mode == 'all':
                x = fun_conv1_features(x, weights)
                x = fun_conv2_features(x, weights)
                x = fun_conv3_features(x, weights)
                x = fun_conv4_features(x, weights)
                x = fun_conv5_features(x, weights)
            x = fun_deeplab_assp(x, weights, is_train=is_train)
        return x

    def set_learnable_params(self, layers):
        print ('Set meta-learning parameters:', end=' ')
        for k, p in self.named_parameters():
            if any([k.startswith(l) for l in layers]):
                p.requires_grad = True
                print (k, end=' ')
            else:
                p.requires_grad = False
        print ('\n')

    def get_learnable_params(self):
        params = OrderedDict()
        for k, p in self.named_parameters():
            if p.requires_grad:
                params[k] = p
        return params

    def copy_meta_weights(self, meta_weights):
        for k, p in self.named_parameters():
            if p.requires_grad and k in meta_weights.keys():
                p.data = meta_weights[k].data.clone()


# network_cfg = [64, 64, 'M2', 128, 128, 'M2', 256, 256, 256, 'M2', 512, 512, 512, 'M1', 512, 512, 512, 'M1']
def Vgg_Deeplab(num_classes=21, meta_training=False):
    if not meta_training:
        model = Vgg_Seg(num_classes)
    else:
        model = Vgg_Meta_Seg(num_classes)
    return model

