import math
from time import time

class PID:

    def __init__(self,name, Kp, Ki, Kd, max_integral, min_interval = 0.001, set_point = 0.0, last_time = None):
        self._Kp           = Kp #percentage
        self._Ki           = Ki #i
        self._Kd           = Kd #different
        self._oriKp = Kp  # percentage
        self._oriKi = Ki  # i
        self._oriKd = Kd  # different
        self._min_interval = min_interval
        self._max_integral = max_integral #10 or 0.5
        self.name          = name
        self._set_point    = set_point
        self._last_time    = last_time if last_time is not None else time()
        self._p_value      = 0.0
        self._i_value      = 0.0
        self._d_value      = 0.0
        self._d_time       = 0.0
        self._d_error      = 0.0
        self._last_error   = 0.0
        self._output       = 0.0
        self.brakes        = 0.001
        self.velocy        = 0.01
        self.increase=0.01
        self.decrease=0.001
        self.current_increase=-1
        self.stability     = True
        self.variant_begin_save=False
        self.current_angle = -100
        self.last_steering_angle=-100
        self.steering_variant = []
        self.step=0
        self.keep_steps=0
        self.current_action=0
        self.need_to_keep=False
        self.keep_time=0
        self.complete_trans=False
        self.complete_trans_step=0
        self.is_find_the_parameters=False
        self.kp_decrease=0.001
        self.ki_decrease = 0.0001
        self.kd_decrease=0.001
        self.record=[]
        self.is_turn=False
        self.turn_angle=0
        self.turn_count=0

    def pid_reset(self):
        self._Kp=self._oriKp
        self._Ki=self._oriKi
        self._Kd=self._oriKd
        self._last_time = time()
        self._p_value = 0.0
        self._i_value = 0.0
        self._d_value = 0.0
        self._d_time = 0.0
        self._d_error = 0.0
        self._last_error = 0.0
        self._output = 0.0
        self.current_increase = -1
        self.stability = True
        self.variant_begin_save = False
        self.current_angle = -100
        self.last_steering_angle = -100
        self.steering_variant = []
        self.step = 0
        self.keep_steps = 0
        self.current_action = 0
        self.need_to_keep = False
        self.keep_time = 0
        self.complete_trans = False
        self.complete_trans_step = 0
        self.is_find_the_parameters = False
        self.record = []
        self.is_turn = False
        self.turn_angle = 0
        self.turn_count = 0

    def stability_of_wheel(self,wheel_variants):
        variant_diff=1
        variant_count=0
        current_site=-1
        # for i in range (len(wheel_variants)):
        #     if math.fabs(wheel_variants[i]) >= 0.01:
        #         if current_site==-1:
        #             current_site=i
        #             variant_diff = wheel_variants[i]
        #         else:
        #             if math.fabs(current_site-i)==1:
        #                 if wheel_variants[i] > 0:
        #                     if variant_diff < 0:
        #                         variant_count += 1
        #                     variant_diff = wheel_variants[i]
        #                 else:
        #                     if variant_diff > 0:
        #                         variant_count += 1
        #                     variant_diff = wheel_variants[i]
        #                 current_site=i
        #             else:
        #                 current_site=i
        #                 variant_diff = wheel_variants[i]
        # stability = variant_count / (len(wheel_variants) * 1.0)
        # return stability
        for variant in wheel_variants:
            if math.fabs(variant)>=0.01:
                if variant_diff==1:
                    variant_diff=variant
                if variant>0:
                    if variant_diff<0:
                        variant_count+=1
                    variant_diff = variant
                else:
                    if variant_diff>0:
                        variant_count+=1
                    variant_diff = variant
        stability=variant_count / (len(wheel_variants) * 1.0)
        return stability

    def stability_of_wheel_2(self,wheel_variants):
        keep_stable=0
        count=0
        stability=0
        for i in range (len(wheel_variants)):
            if math.fabs(wheel_variants[i]) >= 0.05:
                keep_stable+=math.fabs(wheel_variants[i])
                count+=1
        if count!=0:
            stability=keep_stable/(count*1.0)
        return stability

    def save_steering_angle(self,angle_value):
        self.steering_variant.append(angle_value)

    def update_speed(self,angle_value,speed_value,d_time,d_error,cur_time,error):
        self.save_steering_angle(angle_value)
        self._p_value = error
        self._i_value = min(max(error * d_time, -self._max_integral), self._max_integral)
        self._d_value = d_error / d_time if d_time > 0 else 0.0
        if len(self.steering_variant) >= 5:
            probability = self.stability_of_wheel(
                self.steering_variant[(len(self.steering_variant) - 5):len(self.steering_variant)])
            probability2 = self.stability_of_wheel_2(
                self.steering_variant[(len(self.steering_variant) - 5):len(self.steering_variant)])
            #print "probability:{}".format(probability)
            if probability >= 0.2 or probability2>0.7:
                increase_value = 0
                if self.current_increase != -1:
                    increase_value = math.fabs(self.current_increase - 0.05)
                    self.current_increase = -1
                #print "break"

                self._output = self._p_value * self._Kp + self._i_value * self._Ki + self._d_value * self._Kd
                self._d_time = d_time
                self._d_error = d_error
                self._last_time = cur_time
                self._last_error = error

                self._output = self._output - self.brakes - increase_value
                self.stability = False
            else:
                self._output = self._p_value * self._Kp + self._i_value * self._Ki + self._d_value * self._Kd
                self._d_time = d_time
                self._d_error = d_error
                self._last_time = cur_time
                self._last_error = error

                self.current_increase = -1
                self.stability = True
                self.steering_variant = []
        else:
            if self.stability == True:
                self._output = self._p_value * self._Kp + self._i_value * self._Ki + self._d_value * self._Kd
                self._d_time = d_time
                self._d_error = d_error
                self._last_time = cur_time
                self._last_error = error

                #print "speed up"
                if self.current_increase == -1:
                    self.current_increase = self.velocy
                else:
                    self.current_increase += self.increase
                self._output += self.current_increase
            else:
                self._output = self._p_value * self._Kp + self._i_value * self._Ki + self._d_value * self._Kd
                self._d_time = d_time
                self._d_error = d_error
                self._last_time = cur_time
                self._last_error = error

    def update_wheel(self,angle_value,d_time,d_error,cur_time,error):
        self.save_steering_angle(angle_value)
        self._p_value = error
        self._i_value = min(max(error * d_time, -self._max_integral), self._max_integral)
        self._d_value = d_error / d_time if d_time > 0 else 0.0
        if len(self.steering_variant) >= 3:
            probability = self.stability_of_wheel_2(self.steering_variant[(len(self.steering_variant) - 3):len(self.steering_variant)])
            if probability >= 0.1 and probability < 0.7:
                if self._Kp > 0.06:
                    self._Kp -= self.kp_decrease
                if self._Ki > 0.003:
                    self._Ki -= self.ki_decrease
                if self._Kd > 0.03:
                    self._Kd -= self.kd_decrease
                self.stability = False
            elif probability >= 0.7:
                if self._Kp > 0.18:
                    self._Kp -= self.kp_decrease
                if self._Ki > 0.008:
                    self._Ki -= self.ki_decrease
                if self._Kd > 0.08:
                    self._Kd -= self.kd_decrease
                self.stability = False
                self._Kp = 0.18
                self._Ki = 0.008
                self._Kd = 0.08
            else:
                self.current_increase = -1
                self.stability = True
                self.steering_variant = []

            self._output = self._p_value * self._Kp + self._i_value * self._Ki + self._d_value * self._Kd
            self._d_time = d_time
            self._d_error = d_error
            self._last_time = cur_time
            self._last_error = error
        else:
            if self.stability == True:
                if self._Kp < 0.18:
                    self._Kp += self.kp_decrease
                if self._Ki < 0.008:
                    self._Ki += self.ki_decrease
                if self._Kd < 0.08:
                    self._Kd += self.kd_decrease
                self._Kp = 0.18
                self._Ki = 0.008
                self._Kd = 0.08
            self._output = self._p_value * self._Kp + self._i_value * self._Ki + self._d_value * self._Kd
            self._d_time = d_time
            self._d_error = d_error
            self._last_time = cur_time
            self._last_error = error
        self._output *= 1.3

    def update(self,cur_value1, cur_value, cur_time = None):

        if cur_time is None:
            cur_time = time()

        error   = self._set_point - cur_value #Different with zero
        d_time  = cur_time - self._last_time #Time interval
        d_error = error - self._last_error # differencial error

        if d_time >= self._min_interval: #0.001
            if self.name!="wheel":
                self.update_speed(cur_value1,cur_value,d_time,d_error,cur_time,error)
            else:
                self.update_wheel(cur_value1, d_time, d_error, cur_time, error)

        return self._output,self._Kp,self._Ki,self._Kd

    def reset(self, last_time = None, set_point = 0.0):
        self._set_point    = set_point
        self._last_time    = last_time if last_time is not None else time()
        self._p_value      = 0.0
        self._i_value      = 0.0
        self._d_value      = 0.0
        self._d_time       = 0.0
        self._d_error      = 0.0
        self._last_error   = 0.0
        self._output       = 0.0

    def assign_set_point(self, set_point):
        self._set_point = set_point

    def get_set_point(self):
        return self._set_point

    def get_p_value(self):
        return self._p_value

    def get_i_value(self):
        return self._i_value

    def get_d_value(self):
        return self._d_value

    def get_delta_time(self):
        return self._d_time

    def get_delta_error(self):
        return self._d_error

    def get_last_error(self):
        return self._last_error

    def get_last_time(self):
        return self._last_time

    def get_output(self):
        return self._output
