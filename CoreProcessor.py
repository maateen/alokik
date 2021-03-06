import numpy as num
from PIL import Image
from itertools import product
from multiprocessing import get_logger
from os.path import basename
from os.path import dirname
from os.path import join

LOG = get_logger()


def process_image(imfile, formcfg):
    """Process input test image returning answer choices"""
    LOG.setLevel(20)
    LOG.info(basename(imfile))
    LOG.setLevel(30)
    return Map(**formcfg).from_file(imfile)


class Map:

    size = [0, 0]
    offset = [0, 0]
    pos = [0, 0]
    bub = [0, 0]
    space = [0, 0]

    info = None
    score = None
    refzone = None

    expected_dpi = [0, 0]
    expected_size = [0, 0]
    size_tolerance = [0, 0]
    refrc = 0, 0
    contrast = 0.0 * 255
    trim_std = 0
    radius = 0
    min_ref = 0.0 * 255
    signal = 0.0

    def __init__(self, **kwargs):
        """initialize form, calculate default coordinates.  """
        self.__dict__.update(kwargs)
        self._calc_coords()

    def from_file(self, imfile):
        """process image from file.

        import image, fit reference, read answer choices, write output.
        """
        img = self.import_image(imfile)
        img = self.fit_reference(img)
        img, choices = self.get_choices(img)
        self.write_validation(img, imfile)
        return choices

    def import_image(self, imfile):
        """load image, check dpi, trim margins, check size fit image reference boxes"""
        img = self._load_image(imfile)
        img = self._trim_margins(img)
        self._check_size(img)
        return img

    def fit_reference(self, img):
        """fit the reference boxes and draw fit validation"""
        if self.refzone:
            meanfit, fit = self._get_reference_fit(img)
            img = self._overlay_ref_fit(img, meanfit, fit)
            self._set_offset(*meanfit)

        return img

    def get_choices(self, img):
        """read answer choices and overlay validation"""
        means = self._get_bubble_means(img)
        choices = self._choose_answers(means)
        img = self._overlay_bubble_means(img, means)
        return img, choices

    def write_validation(self, img, imfile):
        """ write output validation image"""
        self._save_validation(img, imfile)
        self._save_info_image(img, imfile)

    def _calc_coords(self):
        """calculate (m, n, 4) sized matrix of answer bubble
        hmin,hmax,wmin,wmax coordinates"""
        i = num.outer(num.arange(self.size[0]), num.ones(self.size[1]))
        i0 = self.pos[0] + (i * self.space[0])
        i1 = self.pos[0] + (i * self.space[0]) + self.bub[0]

        j = num.outer(num.ones(self.size[0]), num.arange(self.size[1]))
        j0 = self.pos[1] + (j * self.space[1])
        j1 = self.pos[1] + (j * self.space[1]) + self.bub[1]

        self.coords = num.dstack((i0, i1, j0, j1)).astype('i')

    def _set_offset(self, r=0, c=0):
        """update positional parameters with offset, recalculate
        extracted rectangles and coordinates matrix"""
        self.offset = num.array(self.offset) + num.array([r, c])
        self.pos = [self.pos[0] + r, self.pos[1] + c]

        if self.info:
            self.info = num.array(self.info) + num.array([r, r, c, c])

        if self.score:
            self.score = num.array(self.score) + num.array([r, r, c, c])

        self._calc_coords()

    def _load_image(self, imfile):
        """open input image, correct dpi, return greyscale array"""
        im = Image.open(str(imfile))
        dpi_ratio = num.true_divide(
            self.expected_dpi, num.array(im.info['dpi']))
        newsize = (num.array(im.size) * dpi_ratio).astype('i')
        if not all(newsize == num.array(im.size)):
            im = im.resize(newsize, Image.BICUBIC)
        img = num.array(im.convert('L'))  # convert to greyscale array 0-255
        return img

    def _trim_margins(self, img):
        """Recursivly trim blank edges (low stdev) from input array"""
        oldsize = (0, 0)
        while oldsize != img.shape:  # while the size is changing
            oldsize = img.shape
            for i in range(4):  # 4 times
                img = num.rot90(img)  # rotate 90
                if num.std(img[0, :]) < self.trim_std:  # if low std
                    img = img[1:, :]  # trim edge

        return img

    def _check_size(self, img):
        """Check input image dimensions are within form tolerance. """
        absdiff = num.abs(num.subtract(img.shape, self.expected_size))
        pctdiff = num.true_divide(absdiff, self.expected_size)
        if not num.all(pctdiff <= self.size_tolerance):
            raise StandardError('image size outside form tolerance {} != {}'
                                .format(img.shape, self.expected_size))

    def _get_reference_fit(self, img):
        """Get the best translation offset by fitting black box
        reference zones"""
        bw_img = 255 * (img >= self.contrast)
        fit = [center_on_box(bw_img, self.radius, self.min_ref, *ref)
               for ref in self.refzone]
        meanfit = num.mean(
            num.ma.masked_array(fit, fit == -9999), axis=0).astype('i')
        if meanfit[0] is num.ma.masked:
            raise StandardError('At least one reference box match required')

        return meanfit, fit

    def _get_bubble_means(self, img):
        """get the mean pixel value in each answer bubble region"""
        bw_img = 255 * (img >= self.contrast)
        means = num.zeros(self.coords.shape[:2])
        for (i, j) in product(*map(range, self.size)):
            i0, i1, j0, j1 = self.coords[i, j, :]
            means[i, j] = num.mean(bw_img[i0:i1, j0:j1])

        return means

    def _choose_answers(self, means):
        """choose darkest answer choice. assign poor signal choices -1"""
        choice = num.argmin(means, axis=1)
        if self.signal:
            sorted_rows = num.sort(means, axis=1)
            signal = sorted_rows[:, 1] / sorted_rows[:, 0]
            choice[signal <= self.signal] = -1

        return choice

    def _overlay_ref_fit(self, img, mean, fit, off=25):
        """draw crosses at the corners of the initial and fitted
        reference boxes"""

        def plus(img, x, y, val=0, r=10):
            img[x - 1:x, y - r:y + r], img[x - r:x + r, y - 1:y] = val, val
            return img

        if len(self.refzone) != 4:
            return img

        centers = [(self.ref_rc[0] - off, self.ref_rc[1] - off),
                   (self.ref_rc[0] - off, self.ref_rc[1] + off),
                   (self.ref_rc[0] + off, self.ref_rc[1] - off),
                   (self.ref_rc[0] + off, self.ref_rc[1] + off)]

        # final mean offset
        img = plus(img, self.ref_rc[0], self.ref_rc[1], val=150, r=15)
        img = plus(
            img, self.ref_rc[0] + mean[0], self.ref_rc[1] + mean[1], val=0)
        for [x0, x1, y0, y1], [x_off, y_off], (cx, cy) in zip(self.refzone, fit, centers):
            img = plus(img, cx, cy, val=120, r=15)  # panel fitted
            img = plus(img, cx + x_off, cy + y_off, val=0)  # panel reference
            img = plus(img, x0, y0, val=150)  # expected reference
            img = plus(img, x1, y1, val=150)  #
            img = plus(img, x0 + x_off, y0 + y_off, val=0)  # actual fitted
            img = plus(img, x1 + x_off, y1 + y_off, val=0)  #

        return img

    def _overlay_bubble_means(self, img, means):
        """overlay the bubble region mean values onto the validation image"""
        for (i, j) in product(*map(range, self.size)):
            i0, i1, j0, j1 = self.coords[i, j, :]
            img[i0:i1, j0:j1] = means[i, j]

        return img

    def _save_validation(self, img, imfile):
        """extract the Map info box region and stack the score box"""
        val_file = join(dirname(imfile), 'OMR', 'validation', basename(imfile))
        Image.fromarray(img).save(val_file)

    def _save_info_image(self, img, imfile):
        if len(self.info):
            xmin, xmax, ymin, ymax = self.info
            nameimg = num.rot90(img[xmin:xmax, ymin:ymax])

            if len(self.score):
                xmin, xmax, ymin, ymax = self.score
                score = num.rot90(img[xmin:xmax, ymin:ymax])
                nameimg = num.hstack([nameimg[30:75, :], score])

            name_file = join(
                dirname(imfile), 'OMR', 'names', basename(imfile)[:-3] + 'png')
            Image.fromarray(nameimg).save(name_file)


def center_on_box(img, radius, min_ref, xmin, xmax, ymin, ymax, na_val=-9999):
    """Find the best offset for a black box by trying all within a
    circular search radius


    parameters::

        img         input numpy array image
        radius      search radius for best offset
        min_ref     max mean value for successful match
        xmin,xmax,  initial rectangle region
        na_val      returned offset value if fitting failed

    """
    x, y = num.meshgrid(
        num.arange(-radius, radius), num.arange(-radius, radius))
    coords = [(i, j) for i, j in zip(x.flatten(), y.flatten())
              if (i ** 2 + j ** 2) ** 0.5 <= radius]
    fit = [num.mean(img[(xmin + i):(xmax + i), (ymin + j):(ymax + j)])
           for i, j in coords]
    if num.nanmin(fit) <= min_ref:
        return num.array(coords[num.nanargmin(fit)])
    else:
        return num.array([na_val, na_val])
